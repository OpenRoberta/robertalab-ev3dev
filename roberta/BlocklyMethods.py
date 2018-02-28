import logging
import math
import os
from functools import reduce

logger = logging.getLogger('roberta.blocklymethods')


class BlocklyMethods:
    GOLDEN_RATIO = (1 + math.sqrt(5)) / 2

    @staticmethod
    def isEven(number):
        return (number % 2) == 0

    @staticmethod
    def isOdd(number):
        return (number % 2) == 1

    @staticmethod
    def isPrime(number):
        for i in range(2, math.sqrt(number)):
            remainder = number % i
            if remainder == 0:
                return False
        return True

    @staticmethod
    def isWhole(number):
        return number % 1 == 0

    @staticmethod
    def isPositive(number):
        return number > 0

    @staticmethod
    def isNegative(number):
        return number < 0

    @staticmethod
    def isDivisibleBy(number, divisor):
        return number % divisor == 0

    @staticmethod
    def remainderOf(divident, divisor):
        return divident % divisor

    @staticmethod
    def clamp(x, min_val, max_val):
        return min(max(x, min_val), max_val)

    # note: we don't use the random module since it is large
    @staticmethod
    def randInt(min_val, max_val):
        val = int.from_bytes(os.urandom(4), byteorder='big')
        if min_val < max_val:
            return min_val + (val % ((max_val - min_val) + 1))
        else:
            return max_val + (val % ((min_val - max_val) + 1))

    @staticmethod
    def randDouble():
        return 1.0*int.from_bytes(os.urandom(4), byteorder='big') / 0xffffffff

    @staticmethod
    def textJoin(*args):
        return ''.join(str(arg) for arg in args)

    @staticmethod
    def length(_list):
        return len(_list)

    @staticmethod
    def isEmpty(_list):
        return not _list

    @staticmethod
    def createListWith(*args):
        return list(args)

    @staticmethod
    def createListWithItem(item, times):
        return [item] * times

    @staticmethod
    def listsGetSubList(_list, startLocation, startIndex, endLocation, endIndex):
        fromIndex = BlocklyMethods._calculateIndex(_list, startLocation, startIndex)
        toIndex = 1 + BlocklyMethods._calculateIndex(_list, endLocation, endIndex)
        return _list[fromIndex:toIndex]

    @staticmethod
    def findFirst(_list, item):
        try:
            return _list.index(item)
        except ValueError:
            return -1

    @staticmethod
    def findLast(_list, item):
        try:
            return (len(_list) - 1) - _list[::-1].index(item)
        except ValueError:
            return -1

    @staticmethod
    def listsGetIndex(_list, operation, location, index=None):
        index = BlocklyMethods._calculateIndex(_list, location, index)
        return BlocklyMethods._executeOperation(_list, operation, index, None)

    @staticmethod
    def listsSetIndex(_list, operation, element, location, index=None):
        index = BlocklyMethods._calculateIndex(_list, location, index)
        BlocklyMethods._executeOperation(_list, operation, index, element)

    @staticmethod
    def sumOnList(_list):
        return sum(_list)

    @staticmethod
    def minOnList(_list):
        return min(_list)

    @staticmethod
    def maxOnList(_list):
        return max(_list)

    @staticmethod
    def averageOnList(_list):
        return float(sum(_list)) / len(_list)

    @staticmethod
    def medianOnList(_list):
        n = len(_list)
        if not n:
            return 0
        _list = sorted(_list)
        m = n // 2
        if n % 2 == 0:  # even
            return float(sum(_list[m - 1: m + 1])) / 2.0
        else:
            return _list[m]

    @staticmethod
    def standardDeviatioin(_list):
        n = len(_list)
        if not n:
            return 0
        mean = BlocklyMethods.averageOnList(_list)
        var = float(reduce(lambda x, y: x + math.pow(y - mean, 2), _list)) / n
        return math.sqrt(var)

    @staticmethod
    def randOnList(_list):
        return _list[BlocklyMethods.randInt(0, len(_list) - 1)]

    @staticmethod
    def modeOnList(_list):
        # find which elements are most frequent in the list and
        # returns a list fo them
        modes = []
        # Using a lists of [item, count] to keep count rather than dict to
        # avoid "unhashable" errors when the counted item is itself a list or dict
        counts = []
        maxCount = 1
        for item in _list:
            found = False
            for count in counts:
                if count[0] == item:
                    count[1] += 1
                    maxCount = max(maxCount, count[1])
                    found = True
            if not found:
                counts.append([item, 1])
        for counted_item, item_count in counts:
            if item_count == maxCount:
                modes.append(counted_item)
        return modes

    @staticmethod
    def _calculateIndex(_list, location, index):
        if location is 'from_start':
            return index
        elif location is 'from_end':
            return len(_list) - 1 - index
        elif location is 'first':
            return 0
        elif location is 'last':
            return len(_list) - 1
        elif location is 'random':
            return BlocklyMethods.randInt(0, len(_list) - 1)
        else:
            logger.info('unknown location type [%s]' % location)

    @staticmethod
    def _executeOperation(_list, operation, index, element):
        result = _list[index]
        if operation is 'set':
            _list[index] = element
        elif operation is 'insert':
            _list[index:index] = [element]
            result = element
        elif operation is 'get':
            pass
        elif operation in ['remove', 'get_remove']:
            del _list[index]
        else:
            logger.info('unknown operation [%s]' % operation)
        return result
