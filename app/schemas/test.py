# dict1 = {'a':10, 'b':20, 'c':40, 'd':30}
# dict2 = sorted(dict1.keys,dict1.values, key=lambda x:[dict1.values] )
# print(dict2)
# import random
#
# list1=[random.randint(1,100) for i in range(10)]
# print(list1)
#


dict1 = {'a':10, 'b':20, 'c':40, 'd':30}
dict2 = sorted(dict1.items(), key=lambda x:[dict1.values] )
print(dict2)