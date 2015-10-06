import yaml
from collections import OrderedDict

class UnsortableList(list):
    def sort(self, *args, **kwargs):
        pass

class UnsortableOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))


d = UnsortableOrderedDict([('z', 0),('y', 0),('x', 0)])
Dumper = yaml.SafeDumper
Dumper.ignore_aliases = lambda self, data: True
Dumper.add_representer(UnsortableOrderedDict, yaml.representer.SafeRepresenter.represent_dict)
print yaml.dump(d, default_flow_style=False, Dumper=Dumper)