import random
class_list1 = []
class_list2 = []
class_list3 = []
teacher_list = ['A','B','C','D','E']

class_dict = {1:class_list1, 2:class_list2, 3:class_list3}

for t in teacher_list :
	class_dict[random.randint(1,4)].append(t)

print(class_list1)
print(class_list2)
print(class_list3)



