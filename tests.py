import string
from unittest import TestCase

from analyzer import Analyzer


class AnalyzerTestCase(TestCase):

    def test_normalize_rules(self):
        rules = {
            '<A>': ('abc<B>', '<B>z'),
            '<B>': ('z', ),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        a.rules = a.normalize_rules(a.rules)

        expected = {
            '<A>': [['a', 'b', 'c', '<B>'], ['<B>', 'z']],
            '<B>': [['z']],
        }
        self.assertDictEqual(expected, a.rules)

    def test_get_first(self):
        rules = {
            '<A>': ('abc<B>', '<B>z'),
            '<B>': ('z', '<C>'),
            '<C>': ('d', ),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        a.rules = a.normalize_rules(a.rules)
        print(a.rules)

        self.assertListEqual(a.get_first('a'), ['a'])
        self.assertListEqual(a.get_first('b'), ['b'])
        self.assertListEqual(a.get_first('c'), ['c'])
        self.assertListEqual(a.get_first('d'), ['d'])
        self.assertListEqual(a.get_first('z'), ['z'])
        self.assertListEqual(a.get_first('<A>'), ['a', 'z', 'd'])
        self.assertListEqual(a.get_first('<B>'), ['z', 'd'])
        self.assertListEqual(a.get_first('<C>'), ['d'])

    def test_get_follow(self):
        rules = {
            '<A>': ('abc<B>', '<B>z'),
            '<B>': ('z', '<C>'),
            '<C>': ('d',),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        a.rules = a.normalize_rules(a.rules)
        self.assertSetEqual(a.get_follow('<B>'), {'z'})

        rules = {
            '<A>': ('abc<B><A>', '<B>z'),
            '<B>': ('z', '<C>'),
            '<C>': ('d',),
        }
        a = Analyzer(rules, terms)
        a.rules = a.normalize_rules(a.rules)
        self.assertSetEqual(set(), a.get_follow('<A>'))
        self.assertSetEqual(a.get_follow('<B>'), set(['z'] + a.get_first('<A>')))
        self.assertSetEqual(a.get_follow('<C>'), set())

    def test_normalize_rules_right(self):
        a = Analyzer({}, set())
        self.assertListEqual(['<A>', *list('bcd')], a.normalize_rules_right('<A>bcd'))

    def test_transition_table(self):
        rules = {
            '<A>': ('<B>cd', ),
            '<B>': ('d', )
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        self.assertEqual({('<A>', 'd'): ['<B>', 'c', 'd'], ('<B>', 'd'): ['d']}, a.transition_table)
        rules = {
            '<A>': ('abc<B><A>', '<B>z'),
            '<B>': ('z', '<C>'),
            '<C>': ('d',),
        }
        terms = set(*string.ascii_lowercase.split())
        a = Analyzer(rules, terms)
        self.assertEqual(
            {
                ('<A>', 'a'): ['a', 'b', 'c', '<B>', '<A>'],
                ('<A>', 'z'): ['<B>', 'z'],
                ('<A>', 'd'): ['<B>', 'z'],
                ('<B>', 'z'): ['z'],
                ('<B>', 'd'): ['<C>'],
                ('<C>', 'd'): ['d']
            },
            a.transition_table
        )

    def test_analyze(self):
        rules = {
            '<S>': ('<F>', '(<S>+<F>)'),
            '<F>': ('1',)
        }
        terms = {'1', '+'}
        a = Analyzer(rules, terms)
        print(a.analyze('(1+1)', '<S>'))

        with self.assertRaises(ValueError):
            a.analyze('(1+2)', '<S>')

        with self.assertRaises(ValueError):
            a.analyze('(1+1)abc', '<S>')

    def test_split_rules_right(self):

        a = Analyzer({}, {'AA', 'BB', 'C'})
        self.assertEqual(['AA', 'BB', 'C', '<V>'], a.split_rules_right('AABBC<V>'))
