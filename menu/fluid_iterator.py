import uuid
import enum
import types
import collections

@enum.unique
class ChangeType(enum.Enum):
    insertion = 1
    deletion = 2
    reorder = 3
    sliceChange = 4


def getSliceValues(sliceObj, arrayLen):
    # slice object variables can be None, meaning that they should be
    # interpreted as their default values
    #
    # for negative steps the default end value is "-1-len(array)"
    # this will mean that the returned values aren't useful in range statements
    # unless the arrayLen is added back onto the stop value in the case of -ve
    # step values
    
    step  = sliceObj.step  if (sliceObj.step  is not None) else 1
    start = sliceObj.start if (sliceObj.start is not None) else 0
    if step > 0:
        stop = sliceObj.stop if (sliceObj.stop is not None) else arrayLen
    else:
        stop = sliceObj.stop if (sliceObj.stop is not None) else (-1 - arrayLen)
    
    return (start, stop, step)

# end getSliceValues


def getSubscritionFunctionClosures():
    
    fluid_subscribedFunctions = {}
    
    # listChanged
    def listChanged(sliceObj, changeType, **kwargs):
        # call each of the subscribed functions
        for key in fluid_subscribedFunctions:
            fluid_subscribedFunctions[key](sliceObj, changeType, **kwargs)
    
    # subscribe and unsubscribe
    # add a function to be called when the interable gets changed
    def fluid_subscribe(func):
        newFuncUuid = uuid.uuid1()
        fluid_subscribedFunctions[newFuncUuid] = func
        return newFuncUuid

    def fluid_unsubscribe(funcUuid):
        if funcUuid in fluid_subscribedFunctions:
            del fluid_subscribedFunctions[funcUuid]
        else:
            raise LookupError("cannot unsubscribe funcUuid " + funcUuid + " Doesn't exist")
    
    return (listChanged, fluid_subscribe, fluid_unsubscribe)
    
# end getSubscritionFunctionClosures

# inheriting from MutableSequence allows us to call functions like apppend
# even though these functions are not defined explicitly they will use the
# insert method
class FluidIterable(collections.MutableSequence):
    
    # what  about sorting, reversing and reordering?
    # would be nice to move the index of the current iteration value
    # to where ever the current value moved to in the list.
    # could use the identity of the objects using "is" comparison method
    # the trouble with the identity of objects is that they can be the same
    # for two diffenent variables, i.e. between small integers and strings
    #
    # a = [9, 9]
    # a[0] is a[1]  # is True, so can't tell the order
    # b = ['hello world', 'hello world']
    # b[0] id b[1]  # is True, so can't tell the order
    #
    # conclusion:
    # index munging is the only way
    # overload sort and reverse to get the new indicies
    
    def __init__(self, fixedIterable):
        self.fixedIterable = fixedIterable
        subFuncsTuple = getSubscritionFunctionClosures()
        self.listChanged = subFuncsTuple[0]
        self.fluid_subscribe  = subFuncsTuple[1]
        self.fluid_unsubscribe = subFuncsTuple[2]
    
    def __iter__(self):
        return FluidIterator(self, self.fluid_subscribe, self.fluid_unsubscribe)
    
    # called when inserting using a slice
    # l[:0] = ['a']  # will insert 'g' as the first element in the list
    # slice on the left is effectly removed from the array and replaced
    # with the array on the right. 
    # The slice on the left can be a different size to the array on the right
    # if and only if the slice has a step size of 1.
    def __setitem__(self, sliceObj, v):
        origRtn = self.fixedIterable.__setitem__(sliceObj, v)
        # if the sliceObj is just an integer then the list won't change
        # size or be reodered in any way and therefore the iterator will
        # be uneffected.
        if isinstance(sliceObj, slice):
            self.listChanged(sliceObj, ChangeType.sliceChange, insertionLen=len(v))
        return origRtn

    def __delitem__(self, sliceObj):
        origRtn = self.fixedIterable.__delitem__(sliceObj)
        self.listChanged(sliceObj, ChangeType.deletion)
        return origRtn
    
    # called by append and extend
    def insert(self, sliceObj, value):
        origRtn = self.fixedIterable.insert(sliceObj, value)
        self.listChanged(sliceObj, ChangeType.insertion)
        return origRtn
    
    # a useful function have to implement because can't pass through function
    # calls for built in types like 'list'
    def remove(self, val):
        ind = self.fixedIterable.index(val)
        del self[ind]
    
    def pop(self, *args):
        i = -1
        if args:
            i = args[0]
        origRtn = self.fixedIterable.pop(i)
        self.listChanged(i, ChangeType.deletion)
        return origRtn
    
    # other magic iterable magic methods that need to be accounted for:
    # Magic methods can't be caught by __getattr__ so need to be defined by
    # hand
    #
    # can't get attributes dynamically for built in types
    #
    # def __getattr__(self, attr):
    #    return self.fixedIterable.__getattr__(attr)
    #
    #def __setattr__(self, attr, val):
    #    return self.fixedIterable.__setattr__(attr, val)
    
    def __str__(self):
        return str(self.fixedIterable)
    
    def __repr__(self):
        return self.fixedIterable.__repr__()
        
    def __len__(self): 
        return self.fixedIterable.__len__()
    
    def __getitem__(self, i):
        return self.fixedIterable.__getitem__(i)
    
    def __reversed__(self):
        raise RuntimeError('Reverse is not yet implemented for the fluidIterable class')
        
    def __contains__(self, item):
        return self.fixedIterable.__contains__(item)
        
    def __missing__(self, key):
        return self.fixedIterable.__missing__(key)

# end FluidIterable

    
class FluidIterator:
    def __init__(self, iterable, subFunc, unsubFunc):
        self.subscriptionRef = None
        self.iterableObj = iterable
        self.currentIterableLength = len(self.iterableObj)
        self.currentIndex = -1
        tieInFunc = self.correctIndex  # get function obj (lambda func)
        # add a listener for when the iterable is changed
        self.subscriptionRef = subFunc(tieInFunc)
        self.unSubFunc = unsubFunc
    
    
    # remove the listener to the iterable when the itertor is deleted    
    def __del__(self):
        if self.subscriptionRef:
            self.unSubFunc(self.subscriptionRef)


    def __iter__(self):
        return self
    
    
    # this will be called when the underlying iterable object is changed
    def correctIndex(self, sliceObj, changeType, insertionLen=None):
        # if next has been called at least once so the index is pointing at
        # something sensible
        if self.currentIndex > -1:
            # find the variable that the index was pointing at before the 
            # iterable was changed
            if changeType is ChangeType.insertion:
                self.iterableInsertion(sliceObj)
            elif changeType is ChangeType.deletion:
                self.iterableDeletion(sliceObj)
            elif changeType is ChangeType.sliceChange:
                self.iterableSliceChange(sliceObj, insertionLen)
            elif changeType is ChangeType.reorder:
                raise NotImplementedError('iterable reorder is not implemented yet')
            else:
                raise NotImplementedError('iterable ' + changeType.name + ' is not implemented')
                
        self.currentIterableLength = len(self.iterableObj)


    def incrementHandler(self, addedIndex, incVal):
        # if the "addedIndex" is greater/equal to the current length of 
        # the list, it will be because the list is being extended
        # extending the list will mean the current index does not need to
        # be changed
        if addedIndex >= self.currentIterableLength:
            return
            
        # map any negative indices to positive ones
        i = addedIndex % self.currentIterableLength
        if i <= self.currentIndex:
            # one element has been deleted below the current position,
            # must decrement current position by one.
            self.currentIndex += incVal


    def iterableInsertion(self, insertLoc):
        if isinstance(insertLoc, int):
            self.incrementHandler(insertLoc, 1)
        elif isinstance(insertLoc, slice):
            raise NotImplementedError("INSERTION WITH A SLICE... WHAT?!?")
        else:
            raise NotImplementedError("insertLoc is of type:" + str(type(slice)))
    
    
    def iterableDeletion(self, sliceObj):
        if isinstance(sliceObj, int):
            self.incrementHandler(sliceObj, -1)
        elif isinstance(sliceObj, slice):
            # slice object variables can be None, meaning that they should be
            # interpreted as their default values
            curLen = self.currentIterableLength
            start, stop, step = getSliceValues(sliceObj, curLen)
            deleteLocs = []
            for deleteLoc in range(start, stop, step):
                deleteLocs.append(deleteLoc)
            if step > 0:
                deleteLocs.reverse()
            for deleteLoc in deleteLocs:
                self.incrementHandler(deleteLoc, -1)
        else:
            raise NotImplementedError("sliceObj is of type:" + str(type(sliceObj)))

    
    def iterableSliceChange(self, sliceObj, insertionLen):
        # should be guarenteed to be a slice obj
        if not isinstance(sliceObj, slice):
            raise RuntimeError('SLICE CHANGE WITHOUT A SLICE OBJ... UH OH!')
        
        # slice object variables can be None, meaning that they should be
        # interpreted as their default values
        curLen = self.currentIterableLength
        start, stop, step = getSliceValues(sliceObj, curLen)
        
        # if slice object is "extended" i.e. the selected elements are not
        # contiguous then it is enforced that the insertions are equal to
        # the deletions, therefore the size and ordering of the iterable
        # will not have changed
        if not step == 1:
            return
        
        # step is guarenteed to be '1'
        # if start position of slice is less than the current the index postion
        # then either the entire slice is below the current index and the new
        # value will be pre inserted or the slice contains the current index
        # therefore the current index will move to the next non-deleted value
        # and the inserted value will then be inserted before this point
        # in both cases it counts as "preInsertion" and the index position will
        # have to incremented to accommodate for this
        preInsertion = False
        if start <= self.currentIndex:
            preInsertion = True
        
        # delete the selected elements, position of iterator will be correctly
        # tracked (i.e. self.currentIndex might change)
        self.iterableDeletion(sliceObj)
        
        # if all the new values will be inserted before the current iterator 
        # position i.e. they will not appear at any point during the iteration
        if preInsertion:
            # then the current index location must be incremented to accomodate
            self.currentIndex += insertionLen


    def __next__(self):
        self.currentIndex += 1
        if self.currentIndex < self.currentIterableLength:
            return self.iterableObj[self.currentIndex]
        else:
            self.unSubFunc(self.subscriptionRef)
            self.subscriptionRef = None
            raise StopIteration
            
# end FluidIterator

# this function will overload certain key methods in the provided iterable
# object so that it can be used as FluidIterable, makes a container object
# similar to the FluidIterable class defined below
# this doesn't work for built in types as their methods are read only
# and cannot be overwritten
# def fluidPatch(iterable):
#     
#     subFuncsTuple = getSubscritionFunctionClosures()
#     listChanged = subFuncsTuple[0]
#     fluid_subscribe  = subFuncsTuple[1]
#     fluid_unsubscribe = subFuncsTuple[2]
#     
#     # __iter__
#     if "__iter__" in dir(iterable) and callable(getattr(iterable, "__iter__")):
#         def __iter__(self):
#             return FluidIterator(self, fluid_subscribe, fluid_unsubscribe)
#         # bind __iter__ to iterable, this will overwrite any previous functionality
#         iterable.__iter__ = types.MethodType(__iter__, iterable)
#     else:
#         raise RuntimeError("can only patch iterable objects, i.e. objects with an __iter__ method")
#     
#     # __setitem__
#     if "__setitem__" in dir(iterable) and callable(getattr(iterable, "__setitem__")):
#         origSetItemFunc = iterable.__setitem__
#         def fluid_setitem(self, sliceObj, v):
#             origRtn = origSetItemFunc(sliceObj, v)
#             if isinstance(sliceObj, slice):
#                 listChanged(sliceObj, ChangeType.sliceChange, insertionLen=len(v))
#             return origRtn
#         # bind the overloader setitem function to the iterable
#         iterable.__setitem__ = types.MethodType(fluid_setitem, iterable)
#     
#     # __detitem__
#     if "__delitem__" in dir(iterable) and callable(getattr(iterable, "__delitem__")):
#         origDelItemFunc = iterable.__delitem__
#         def fluid_delitem(self, sliceObj):
#             origRtn = origDelItemFunc(sliceObj)
#             listChanged(sliceObj, ChangeType.deletion)
#             return origRtn
#         # bind the overloaded delitem function to the iterable
#         iterable.__detitem__ = types.MethodType(fluid_delitem, iterable)
# 
#         # remove
#         if "remove" in dir(iterable) and callable(getattr(iterable, "remove")):
#             if not ("index" in dir(iterable) and callable(getattr(iterable, "index"))):
#                 raise AttributeError("to override remove' function an 'index' function must be present")
#             # a useful function have to implement because can't pass through function
#             # calls for built in types like 'list'
#             def fluid_remove(self, val):
#                 ind = iterable.index(val)
#                 fluid_delitem(iterable, ind)
#             # bind the overloaded remove function to the iterable
#             iterable.remove = types.MethodType(fluid_remove, iterable)
#     
#     # insert
#     if "insert" in dir(iterable) and callable(getattr(iterable, "insert")):
#         origInsertFunc = iterable.insert
#         # called by append and extend
#         def fluid_insert(self, sliceObj, value):
#             origRtn = origInsertFunc(sliceObj, value)
#             listChanged(sliceObj, ChangeType.insertion)
#             return origRtn
#         # bind the overloaded insert function to the iterable
#         iterable.insert = types.MethodType(fluid_insert, iterable)
# 
#     
# # end fliudPatch

if __name__ == "__main__":
    
## traditional list iteration behaviour
    
    print('traditional list iteration behaviour')
    
    print(' ')
    print('test 1')
    arr = [0,1,2,3,4,5,6]
    for i in arr:
        print(i)
        print(arr)
        # arr is overwritten but the original array is still 
        # used for the iteration
        arr = [0,1,2]
    
    print(' ')
    print('test 2')
    arr = [0,1,2,3,4,5,6]
    for i in arr:
        print(i)
        print(arr)
        # can modify in place, elements 2, 4 and 6 are removed before the are
        # printed
        if i is 0:
            del arr[2:7:2]
    # output: 0,1,3,5
    # final list: [0,1,3,5]
    
    print(' ')
    print('test 3')
    arr = [0,1,2,3,4,5,6]
    for i in arr:
        print(i)
        print(arr)
        # when modifying in place, the index is not correctly updated, even 
        # though the first element is removed after it has been printed, the
        # the second element (in the orignal list) gets missed
        if i is 0:
            del arr[0]
    # output: 0,2,3,4,5,6
    # final list: [1,2,3,4,5,6]
    
    print(' ')
    print('test 4')
    arr = [0,1,2,3,4,5,6]
    for i, v in enumerate(arr):
        print(v)
        print(arr)
        # when modifying in place, the index is not correctly updated, 
        # first element (in original list) gets printed twice rather than once
        # as it confused by the insertion
        if i is 0:
            arr.insert(0,'a')
    # output: 0,0,1,2,3,4,5,6
    # final list: ['a',0,1,2,3,4,5,6]

## Fluid iteration behaviour

    print('Fluid iteration behaviour')

    print(' ')
    print('test 1')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        # arr is overwritten but the original array is still 
        # used for the iteration
        fluidArr = [0,1,2]

    
    print(' ')
    print('test 2')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        # can modify in place, elements 2, 4 and 6 are removed before the are
        # printed
        if i is 0:
            del fluidArr[2:7:2]
    # output: 0,1,3,5
    # final list: [0,1,3,5]
    
    print(' ')
    print('test 3')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        # when modifying in place, the index is correctly updated, even 
        # though the first element is removed after it has been printed, the
        # the second element (in the orignal list) gets printed next
        if i is 0:
            del fluidArr[0]
    # output: 0,1,2,3,4,5,6
    # final list: [1,2,3,4,5,6]
    
    print(' ')
    print('test 4')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    # get iterator first so can query the current index
    fluidArrIter = fluidArr.__iter__()
    for i, v in enumerate(fluidArrIter):
        print('enum: ', i)
        print('current val: ', v)
        print('current ind: ', fluidArrIter.currentIndex)
        print(fluidArr)
        # when modifying in place, the index is correctly updated, 
        # first element (in original list) gets printed once
        # despite the insertion
        if i is 0:
            fluidArr.insert(0,'a')
    # output: 0,1,2,3,4,5,6
    # final list: ['a',0,1,2,3,4,5,6]
        
    print(' ')
    print('test 5')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        if i is 0:
            fluidArr[:0] = ['a','b','c']
    # output: 0,1,2,3,4,5,6
    # final list: ['a','b','c',0,1,2,3,4,5,6]
            
    print(' ')
    print('test 6')
    print('replacing a section with a section of a different length')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        if i is 0:
            fluidArr[4:5] = ['a','b','c']
    # output: 0,1,2,3,'a','b','c',5,6
    # final list: [0,1,2,3,'a','b','c',5,6]
    
    print(' ')
    print('test 7')
    print('replacing current interating section with a section of the same length')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        if i is 0:
            fluidArr[2::-1] = ['a','b','c']
    # output: 0,'b','a',3,4,5,6
    # final list: ['c','b','a',3,4,5,6]
    
    print(' ')
    print('test 8')
    print('replacing current interating section with a section of a different length')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        if i is 2:
            fluidArr[1:5] = ['a','b','c']
    # output: 0, 1, 2, 5, 6
    # final list: [0, 'a', 'b', 'c', 5, 6]
    
    print(' ')
    print('test 9')
    fluidArr = FluidIterable([0,1,2,3,4,5,6])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        if i is 1:
            print('inner loop start')
            for j in fluidArr:
                print(j)
                print(fluidArr)
                if j is 0:
                    fluidArr[:0] = ['a','b','c']
            print('inner loop ends')
    
    print(' ')
    print('test 10')
    fluidArr = FluidIterable([0,1,2,3,4,5,6,7,8])
    for i in fluidArr:
        print(i)
        print(fluidArr)
        if i is 2:
            print('inner loop start')
            for j in fluidArr:
                print(j)
                print(fluidArr)
                if j%2 == 0:
                    fluidArr.remove(j)
            print('inner loop ends')
    
    print(' ')
    print('test 11')
    l = [0,1,2,3,4,5,6,7,8]  
    fluidL = FluidIterable(l)                       
    for i in fluidL:
        print('initial state of list on this iteration: ' + str(fluidL)) 
        print('current iteration value: ' + str(i))
        print('popped value: ' + str(fluidL.pop(2)))
        print(' ')
    # output: 8,7,6,5,4
    # final list: [0,1,2,3]
    
    print(' ')
    print('test 12')
    fluidArr = FluidIterable([0,1,2,3])
    # get iterator first so can query the current index
    fluidArrIter = fluidArr.__iter__()
    for i, v in enumerate(fluidArrIter):
        print('enum: ', i)
        print('current val: ', v)
        print('current ind: ', fluidArrIter.currentIndex)
        print(fluidArr)
        fluidArr.insert(0,'a')
        print(' ')
        
    print('Final List Value: ' + str(fluidArr))

    
    ## Reduce list to contain no multiples of any other element
    
    print(' ')
    print('use case 1')
    import random
    # randInts = [random.randint(1,100) for _ in range(10)]
    randInts = [70, 20, 61, 80, 54, 18, 7, 18, 55, 9]
    fRandInts = FluidIterable(randInts)
    fRandIntsIter = fRandInts.__iter__()
    for i in fRandIntsIter:
        print(' ')
        print('outer val: ', i)
        innerIntsIter = fRandInts.__iter__()
        for j in innerIntsIter:
            innerIndex = innerIntsIter.currentIndex
            # skip the element that the outloop is currently on
            if not innerIndex == fRandIntsIter.currentIndex:
                # if the element is a multiple of the element that the outer
                # loop is on, remove it
                if j%i == 0:
                    print('remove val: ', j)
                    del fRandInts[innerIndex]
                # end if multiple, then remove
            # end if not the same value as outer loop
        # end inner loop
    # end outerloop
    
    print(randInts)