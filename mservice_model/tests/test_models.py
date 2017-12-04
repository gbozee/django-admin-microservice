import unittest
from unittest import mock
from mservice_model.models import ServiceModel, model_factory
from mservice_model.api import ServiceApi
from .response import MockRequest, option_response, get_all_response

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.base_url = 'http://localhost:2000/todos/'
        self.service = ServiceApi(self.base_url)
        self.patcher = mock.patch('mservice_model.api.requests')
        self.mock_request = self.patcher.start()
        self.mock_get = self.mock_request.get
        self.mock_post = self.mock_request.post
        self.mock_put = self.mock_request.put
        self.mock_options = self.mock_request.options
        self.mock_delete = self.mock_request.delete
        self.mock_options.return_value = MockRequest(option_response,overwrite=True)

    def tearDown(self):
        self.patcher.stop()


class SampleModelTestCase(BaseTestCase):    
        
    def test_can_create_instance_of_class(self):
        SampleModel = model_factory(self.service, name="Sample")
        self.assertEqual(SampleModel.Meta.app_label, 'sample')

    def test_mixin_class_methods_can_be_retrieved(self):
        class Mixin(object):
            def name(self):
                return "Biola"
        SampleModel = model_factory(self.service, "Sample", Mixin)
        self.assertEqual(SampleModel.name(""), "Biola")

    def test_field_types(self):
        SampleModel = model_factory(self.service, name="Sample")
        service_fields = SampleModel._meta._service_fields
        self.assertEqual(service_fields['id'].__class__.__name__, 'AutoField')
        self.assertEqual(service_fields['completed'].__class__.__name__, 'BooleanField')
        self.assertEqual(service_fields['title'].__class__.__name__, 'CharField')
        
    def test_count_method_in_queryset_returns_correct_value(self):
        self.mock_get.return_value = MockRequest(get_all_response, overwrite=True)
        SampleModel = model_factory(self.service, name="Sample")
        self.assertEqual(SampleModel.objects.count(), 4)

    def test_all_methods_returns_all_queryset_result(self):
        self.mock_get.return_value = MockRequest(get_all_response, overwrite=True)
        SampleModel = model_factory(self.service, name="Sample")
        result = SampleModel.objects.all()
        self.assertEqual(result[0].completed, False)
        self.assertEqual(result[0].id, 1)
        self.assertIsNone(result[0].owner)

    def test_get_method_returns_single_object_based_on_query(self):
        self.mock_get.return_value = MockRequest(get_all_response['results'][0], overwrite=True)
        SampleModel = model_factory(self.service, name="Sample")
        result = SampleModel.objects.get(id=1)
        self.mock_get.assert_called_once_with(
            "{}{}/".format(self.base_url, 1), 
        )
        self.assertEqual(result.id, 1)

    def test_can_add_an_item(self):
        self.mock_post.return_value = MockRequest({
            "title":"Hello World","completed":True,"id":72,"owner":None
        },overwrite=True)
        SampleModel = model_factory(self.service, name="Sample")
        result = SampleModel.objects.create(title="Hello world",completed=True)
        self.assertEqual(result.pk, 72)
        self.assertEqual(result.owner,None)
        self.assertEqual(result.title, "Hello World")
        self.assertTrue(result.completed)


    def test_can_update_an_item(self):
        self.mock_get.return_value = MockRequest(
            get_all_response['results'][0], overwrite=True)
        self.mock_put.return_value = MockRequest(
            {
                "id": 1,
                "title": "Buckle my shoe",
                "completed": True,
                "owner": None
            },overwrite=True
        )
        SampleModel = model_factory(self.service, name="Sample")
        result = SampleModel.objects.get(id=1)
        result.completed = True
        result.save()
        self.assertEqual(result.id, 1)
        self.assertTrue(result.completed)
        self.mock_put.assert_called_once_with(
            "{}{}/".format(self.base_url, 1), json={'completed': True, 'owner': None, 'title': 'Buckle my shoe'}
        )

    def test_calling_save_on_a_new_record_does_not_raise_error(self):
        self.mock_post.return_value = MockRequest({
            "title": "Aloiba", "completed": False, "id": 72, "owner": None
        }, overwrite=True)

        SampleModel = model_factory(self.service, name="Sample")
        record = SampleModel()
        record.title = "Aloiba"
        record.completed = False
        self.assertEqual(record.id, None)
        record.save()
        self.mock_post.assert_called_once_with(
            "{}".format(self.base_url),json={'title':"Aloiba",'completed':False, 'owner':None}
        )
        self.assertEqual(record.title,"Aloiba")
        self.assertFalse(record.completed)
        self.assertEqual(record.id,72)

        
