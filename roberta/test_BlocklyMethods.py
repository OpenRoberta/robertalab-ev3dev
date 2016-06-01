import logging
import unittest

from roberta.BlocklyMethods import BlocklyMethods

logging.basicConfig(level=logging.CRITICAL)


class TestBlocklyMethods(unittest.TestCase):
    def test_randInt(self):
        v = BlocklyMethods.randInt(5, 10)
        self.assertGreaterEqual(v, 5)
        self.assertLessEqual(v, 10)

    def test_textJoin_EmptyList(self):
        self.assertEqual("", BlocklyMethods.textJoin())

    def test_textJoin_Single(self):
        self.assertEqual("x", BlocklyMethods.textJoin('x'))

    def test_textJoin_Three(self):
        self.assertEqual("xyz", BlocklyMethods.textJoin('x', 'yz'))

    def test_length(self):
        self.assertEqual(2, BlocklyMethods.length(['x', 'yz']))

    def test_createListWith(self):
        self.assertEqual(['x', 'yz'], BlocklyMethods.createListWith('x', 'yz'))

    def test_createListWithItem(self):
        self.assertEqual(['x', 'x'], BlocklyMethods.createListWithItem('x', 2))

    def test_listsGetSubList_FromStart(self):
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'from_start', 1, 'from_start', 2)
        self.assertEqual(['b', 'c'], sub)

    def test_listsGetSubList_FromEnd(self):
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'from_end', 2, 'from_end', 1)
        self.assertEqual(['b', 'c'], sub)

    def test_listsGetSubList_First(self):
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'first', None, 'first', None)
        self.assertEqual(['a'], sub)

    def test_listsGetSubList_Last(self):
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'last', None, 'last', None)
        self.assertEqual(['d'], sub)

    def test_findFirst_NotFound(self):
        res = BlocklyMethods.findFirst(['a', 'b', 'b', 'd'], 'x')
        self.assertEqual(-1, res)

    def test_findFirst_Found(self):
        res = BlocklyMethods.findFirst(['a', 'b', 'b', 'c'], 'b')
        self.assertEqual(1, res)

    def test_findLast_NotFound(self):
        res = BlocklyMethods.findLast(['a', 'b', 'b', 'd'], 'x')
        self.assertEqual(-1, res)

    def test_findLast_Found(self):
        res = BlocklyMethods.findLast(['a', 'b', 'b', 'c'], 'b')
        self.assertEqual(2, res)

    def test_listsGetIndex_GetFirst(self):
        res = BlocklyMethods.listsGetIndex(['a', 'b', 'c', 'd'], 'get', 'first')
        self.assertEqual('a', res)

    def test_listsGetIndex_RemoveFirst(self):
        items = ['a', 'b', 'c', 'd']
        BlocklyMethods.listsGetIndex(items, 'remove', 'first')
        self.assertEqual(['b', 'c', 'd'], items)

    def test_listsGetIndex_RemoveLast(self):
        items = ['a', 'b', 'c', 'd']
        BlocklyMethods.listsGetIndex(items, 'remove', 'last')
        self.assertEqual(['a', 'b', 'c'], items)

    def test_listsGetIndex_GetFromStart(self):
        res = BlocklyMethods.listsGetIndex(['a', 'b', 'c', 'd'], 'get', 'from_start', 1)
        self.assertEqual('b', res)

    def test_listsSetIndex_SetFirst(self):
        items = ['a', 'b', 'c', 'd']
        BlocklyMethods.listsSetIndex(items, 'set', 'A', 'first')
        self.assertEqual(['A', 'b', 'c', 'd'], items)

    def test_listsSetIndex_SetRandom(self):
        items = ['a', 'b', 'c', 'd']
        BlocklyMethods.listsSetIndex(items, 'set', 'A', 'random')
        self.assertNotEqual(['a', 'b', 'c', 'd'], items)
        self.assertIn('A', items)

    def test_listsSetIndex_InsertFirst(self):
        items = ['a', 'b', 'c', 'd']
        BlocklyMethods.listsSetIndex(items, 'insert', 'A', 'first')
        self.assertEqual(['A', 'a', 'b', 'c', 'd'], items)

    def test_listsSetIndex_InsertFromStart(self):
        items = ['a', 'b', 'c', 'd']
        BlocklyMethods.listsSetIndex(items, 'insert', 'A', 'from_start', 1)
        self.assertEqual(['a', 'A', 'b', 'c', 'd'], items)

    def test_averageOnList(self):
        items = [0, 8, 4, 10]
        res = BlocklyMethods.averageOnList(items)
        self.assertEqual(5.5, res)

    def test_medianOnList(self):
        items = [0, 8, 4, 10]
        res = BlocklyMethods.medianOnList(items)
        self.assertEqual(6.0, res)

    def test_standardDeviatioin(self):
        items = [0, 8, 4, 10]
        res = BlocklyMethods.standardDeviatioin(items)
        self.assertAlmostEqual(2.6809513, res)

    def test_randOnList(self):
        items = ['a', 'b', 'c', 'd']
        res = BlocklyMethods.randOnList(items)
        self.assertIn(res, items)

    def test_modeOnList_all(self):
        items = ['a', 'b', 'c', 'd']
        res = BlocklyMethods.modeOnList(items)
        self.assertEqual(items, res)

    def test_modeOnList_One(self):
        items = ['a', 'b', 'a', 'd']
        res = BlocklyMethods.modeOnList(items)
        self.assertEqual(['a'], res)

if __name__ == '__main__':
    unittest.main()
