"""
Tests for the result cache and the waiting-for-the-result logic.

Run them inside the stexaminer container, which has the idp binaries and the
scripts that some of them need:

    python manage.py test api_app

The tests that do not need a real calculation mock out Celery. The ones that
do are skipped when the `idp` command is not available.
"""
import json
import shutil
from datetime import datetime
from unittest import skipUnless
from unittest.mock import MagicMock, patch

from celery.exceptions import TimeoutError as CeleryTimeoutError
from django.test import Client, TestCase

from . import settings
from . execute_calc import run_calc
from . models import Calc, Results
from . tasks import MyCalcTask, flex_parse

GRAPH = 'digraph stemma { "r" -> "A"; "r" -> "B"; "r" -> "C"; "r" -> "D"; }'
OTHER_GRAPH = 'digraph stemma { "r" -> "A"; "r" -> "B"; "r" -> "C"; "r" -> "D"; "r" -> "E"; }'
GROUPINGS = [[['A', 'B'], ['C', 'D']], [['A', 'C'], ['B', 'D']]]


def make_calc(command='findGroupings'):
    return Calc.objects.create(input_data='{}', calculation_type=command,
                               calc_end=datetime.now(),
                               calc_status=settings.STATUS_CODES['finished'])


def store_results(command, groupings, graph=GRAPH, answers=None):
    """Put a calculation's results in the database as if it had run."""
    calc = make_calc(command)
    answers = answers or [[g, True] for g in groupings]
    for grouping, answer in zip(groupings, answers):
        Results.objects.create(calc_id=calc, algorithm=command, stemmastring=graph,
                               grouping=grouping, result=answer)
    return calc


class CalcRequestTestCase(TestCase):

    def setUp(self):
        # The service only answers to the host names it is configured for
        self.client = Client(HTTP_HOST='localhost')

    def post(self, command, groupings=GROUPINGS, graph=GRAPH):
        body = {'content': {'command': command, 'groupings': groupings, 'graph': graph}}
        response = self.client.post('/calc-items/', data=json.dumps(body),
                                    content_type='application/json')
        return response, json.loads(response.content)


class ResultCacheTests(CalcRequestTestCase):

    @patch('api_app.views.run_calc')
    def test_unknown_request_is_calculated(self, run_calc_mock):
        answer = [[g, True] for g in GROUPINGS]
        run_calc_mock.return_value = answer
        response, data = self.post('findGroupings')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['result_source'], 'algorithm')
        self.assertEqual(data['result'], answer)
        run_calc_mock.assert_called_once()

    @patch('api_app.views.run_calc')
    def test_view_does_not_store_results(self, run_calc_mock):
        # Storing is the job of the Celery task, which is the only place that
        # sees the result of a calculation that outlasts the request.
        run_calc_mock.return_value = [[g, True] for g in GROUPINGS]
        self.post('findGroupings')
        self.assertEqual(Results.objects.count(), 0)

    @patch('api_app.views.run_calc')
    def test_stored_results_are_served_without_calculating(self, run_calc_mock):
        answers = [[[['A', 'B', 'r'], ['C', 'D']], True], [[['A', 'C'], ['B', 'D']], False]]
        calc = store_results('findGroupings', GROUPINGS, answers=answers)
        response, data = self.post('findGroupings')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['result_source'], 'database')
        self.assertEqual(data['jobid'], calc.id)
        self.assertEqual(data['result'], answers)
        run_calc_mock.assert_not_called()

    @patch('api_app.views.run_calc')
    def test_results_come_back_in_request_order(self, run_calc_mock):
        calc = store_results('findGroupings', GROUPINGS)
        reverse = list(reversed(GROUPINGS))
        response, data = self.post('findGroupings', groupings=reverse)
        self.assertEqual(data['result_source'], 'database')
        self.assertEqual(data['result'], [[g, True] for g in reverse])

    @patch('api_app.views.run_calc')
    def test_results_of_another_command_are_not_a_hit(self, run_calc_mock):
        # The same groupings were analyzed with findGroupings; asking for
        # findClasses must still calculate, and must not answer with nothing.
        store_results('findGroupings', GROUPINGS)
        classes = [[g, {'source': ['A'], 'copy': ['B'], 'revert': []}] for g in GROUPINGS]
        run_calc_mock.return_value = classes
        response, data = self.post('findClasses')
        self.assertEqual(data['result_source'], 'algorithm')
        self.assertEqual(data['result'], classes)
        run_calc_mock.assert_called_once()

    @patch('api_app.views.run_calc')
    def test_results_for_another_stemma_are_not_a_hit(self, run_calc_mock):
        store_results('findGroupings', GROUPINGS, graph=OTHER_GRAPH)
        run_calc_mock.return_value = [[g, True] for g in GROUPINGS]
        response, data = self.post('findGroupings')
        self.assertEqual(data['result_source'], 'algorithm')
        run_calc_mock.assert_called_once()

    @patch('api_app.views.run_calc')
    def test_partly_stored_request_is_calculated_whole(self, run_calc_mock):
        store_results('findGroupings', GROUPINGS[:1])
        run_calc_mock.return_value = [[g, True] for g in GROUPINGS]
        response, data = self.post('findGroupings')
        self.assertEqual(data['result_source'], 'algorithm')
        self.assertEqual(len(data['result']), len(GROUPINGS))

    @patch('api_app.views.run_calc')
    def test_repeated_groupings_do_not_multiply_results(self, run_calc_mock):
        # The same calculation stored twice, as can happen if two identical
        # requests ran at once
        store_results('findGroupings', GROUPINGS)
        store_results('findGroupings', GROUPINGS)
        response, data = self.post('findGroupings')
        self.assertEqual(data['result_source'], 'database')
        self.assertEqual(len(data['result']), len(GROUPINGS))

    @patch('api_app.views.run_calc')
    def test_slow_calculation_gets_a_job_id(self, run_calc_mock):
        run_calc_mock.return_value = None
        response, data = self.post('findGroupings')
        self.assertEqual(response.status_code, 201)
        self.assertIn('jobid', ' '.join(data.values()))


class RunCalcTests(TestCase):
    """The wait for the Celery result in run_calc."""

    def run_with(self, task_result):
        calc = make_calc()
        with patch('api_app.execute_calc.MyCalcTask') as task:
            task.apply_async.return_value = task_result
            answer = run_calc(d={}, c='findGroupings', obj_id=calc.id, h=None, p=None)
        return answer

    def test_finished_task_gives_its_result(self):
        res = MagicMock(status='SUCCESS')
        res.get.return_value = [['answer']]
        self.assertEqual(self.run_with(res), [['answer']])

    def test_wait_is_limited_and_does_not_raise_task_errors(self):
        res = MagicMock(status='SUCCESS')
        res.get.return_value = []
        self.run_with(res)
        res.get.assert_any_call(timeout=settings.WAIT_FOR_IDPRESULT, propagate=False)

    def test_task_that_outlasts_the_wait_gives_nothing(self):
        res = MagicMock(status='PENDING')
        res.get.side_effect = CeleryTimeoutError()
        self.assertIsNone(self.run_with(res))

    def test_failed_task_gives_nothing(self):
        res = MagicMock(status='FAILURE')
        res.get.return_value = Exception('idp fell over')
        self.assertIsNone(self.run_with(res))


@skipUnless(shutil.which('idp'), 'needs the idp solver')
class TaskStoresResultsTests(CalcRequestTestCase):
    """What the Celery task leaves in the database, using the real solver."""

    def run_task(self, command, groupings=GROUPINGS, graph=GRAPH):
        content = {'command': command, 'groupings': groupings, 'graph': graph}
        calc = Calc.objects.create(input_data=str(content), calculation_type=command,
                                   calc_end=datetime.now(),
                                   calc_status=settings.STATUS_CODES['running'])
        answer = MyCalcTask.run(d=content, c=command, obj_id=calc.id)
        return calc, answer

    def test_one_result_per_grouping_is_stored(self):
        calc, answer = self.run_task('findGroupings')
        self.assertEqual(len(answer), len(GROUPINGS))
        stored = Results.objects.filter(calc_id=calc).order_by('id')
        self.assertEqual(stored.count(), len(GROUPINGS))
        for record, grouping, result in zip(stored, GROUPINGS, answer):
            self.assertEqual(record.algorithm, 'findGroupings')
            self.assertEqual(record.stemmastring, GRAPH)
            self.assertEqual(flex_parse(record.grouping), grouping)
            self.assertEqual(flex_parse(record.result), result)

    @patch('api_app.views.run_calc')
    def test_calculation_that_outlasted_the_request_is_cached(self, run_calc_mock):
        # The request returns before the calculation has finished...
        run_calc_mock.return_value = None
        response, data = self.post('findGroupings')
        calc = Calc.objects.latest('id')
        self.assertEqual(Results.objects.count(), 0)

        # ...and the task finishes some time later.
        content = {'command': 'findGroupings', 'groupings': GROUPINGS, 'graph': GRAPH}
        answer = MyCalcTask.run(d=content, c='findGroupings', obj_id=calc.id)

        # The same request now needs no calculation
        run_calc_mock.reset_mock()
        response, data = self.post('findGroupings')
        run_calc_mock.assert_not_called()
        self.assertEqual(data['result_source'], 'database')
        self.assertEqual(data['result'], answer)

    @patch('api_app.views.run_calc')
    def test_both_commands_can_be_cached_for_the_same_groupings(self, run_calc_mock):
        _, grouped = self.run_task('findGroupings')
        _, classed = self.run_task('findClasses')
        run_calc_mock.side_effect = AssertionError('should have come from the database')
        response, data = self.post('findGroupings')
        self.assertEqual(data['result'], grouped)
        response, data = self.post('findClasses')
        self.assertEqual(data['result'], classed)
