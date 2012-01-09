from stdnet import test
from stdnet.utils import zip

from examples.models import SimpleModel, Person, Group


class LoadOnly(test.TestCase):
    model = SimpleModel
    
    def setUp(self):
        self.model(code = 'a', group = 'group1', description = 'blabla').save()
        self.model(code = 'b', group = 'group2', description = 'blabla').save()
        self.model(code = 'c', group = 'group1', description = 'blabla').save()
        self.model(code = 'd', group = 'group3', description = 'blabla').save()
        self.model(code = 'e', group = 'group1', description = 'blabla').save()
        
    def test_idonly(self):
        qs = self.model.objects.all().load_only('id')
        for m in qs:
            self.assertEqual(m._loadedfields,())
            self.assertEqual(tuple(m.loadedfields()),())
            self.assertFalse(hasattr(m,'code'))
            self.assertFalse(hasattr(m,'group'))
            self.assertFalse(hasattr(m,'description'))
            self.assertTrue('id' in m._dbdata)
            self.assertEqual(int(m._dbdata['id']),m.id)
            
    def test_idonly_None(self):
        qs = self.model.objects.all().load_only('id')
        with transaction(self.model) as t:
            for m in qs:
                self.assertFalse(hasattr(m,'description'))
                m.description = None
                m.save(t)
        # Check that description are empty
        for m in self.model.objects.all().load_only('description'):
            self.assertFalse(m.description)
            
    def test_idonly_delete(self):
        qs = self.model.objects.all().load_only('id')
        qs.delete()
        qs = self.model.objects.filter(group = 'group1')
        self.assertEqual(qs.count(),0)
        
    def testSimple(self):
        qs = self.model.objects.all().load_only('code')
        for m in qs:
            self.assertEqual(m._loadedfields,('code',))
            self.assertTrue(m.code)
            self.assertFalse(hasattr(m,'group'))
            self.assertFalse(hasattr(m,'description'))
        qs = self.model.objects.all().load_only('code','group')
        for m in qs:
            self.assertEqual(m._loadedfields,('code','group'))
            self.assertTrue(m.code)
            self.assertTrue(m.group)
            self.assertFalse(hasattr(m,'description'))
            
    def testSave(self):
        original = [m.group for m in self.model.objects.all()]
        self.assertEqual(self.model.objects.filter(group = 'group1').count(),3)
        qs = self.model.objects.all().load_only('code')
        for m in qs:
            m.save()
        qs = self.model.objects.all()
        for m,g in zip(qs,original):
            self.assertEqual(m.group,g)
        # No check indexes
        self.assertEqual(self.model.objects.filter(group = 'group1').count(),3)
        
    def testChangeNotLoaded(self):
        '''We load an object with only one field and modify a field not
loaded. The correct behavior should be to updated the field and indexes.'''
        original = [m.group for m in self.model.objects.all()]
        qs = self.model.objects.all().load_only('code')
        for m in qs:
            m.group = 'group4'
            m.save()
        qs = self.model.objects.filter(group = 'group1')
        self.assertEqual(qs.count(),0)
        qs = self.model.objects.filter(group = 'group2')
        self.assertEqual(qs.count(),0)
        qs = self.model.objects.filter(group = 'group3')
        self.assertEqual(qs.count(),0)
        qs = self.model.objects.filter(group = 'group4')
        self.assertEqual(qs.count(),5)
        for m in qs:
            self.assertEqual(m.group,'group4')
        
        
class LoadOnlyRelated(test.TestCase):
    models = (Person, Group)
    
    def setUp(self):
        g1 = Group(name = 'bla').save()
        g2 = Group(name = 'foo').save()
        with transaction(Person) as t:
            Person(name = 'luca', group = g1).save(t)
            Person(name = 'carl', group = g1).save(t)
            Person(name = 'bob', group = g1).save(t)
            
    def test_simple(self):
        qs = Person.objects.all().load_only('group')
        for m in qs:
            self.assertEqual(m._loadedfields,('group',))
            self.assertFalse(hasattr(m,'name'))
            self.assertTrue(hasattr(m,'group_id'))
            self.assertTrue(m.group_id)
            self.assertTrue('id' in m._dbdata)
            self.assertEqual(int(m._dbdata['id']),m.id)
            g = m.group
            self.assertTrue(isinstance(g,Group))
            
            