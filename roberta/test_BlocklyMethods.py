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
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'FROM_START', 1, 'FROM_START', 2)
        self.assertEqual(['b', 'c'], sub)

    def test_listsGetSubList_FromEnd(self):
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'FROM_END', 2, 'FROM_END', 1)
        self.assertEqual(['b', 'c'], sub)

    def test_listsGetSubList_First(self):
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'FIRST', None, 'FIRST', None)
        self.assertEqual(['a'], sub)

    def test_listsGetSubList_Last(self):
        sub = BlocklyMethods.listsGetSubList(['a', 'b', 'c', 'd'], 'LAST', None, 'LAST', None)
        self.assertEqual(['d'], sub)

if __name__ == '__main__':
    unittest.main()
