from enum import Flag


class AdvancedType(Flag):
    BASE = 0
    FLITSR = 1
    MULTI = 3  # includes FLITSR (1 + 2)
    ARTEMIS = 4
    PARALLEL = 8
    MUTATION = 16

    def get_file_name(self):
        if (self is AdvancedType.BASE):
            return self.name.lower()  # type: ignore # (BASE always has a name)
        else:
            return "_".join([t.name.lower() for t in
                             list(AdvancedType.__members__.values())[1:]
                             if t in self and t.name])  # type: ignore
