import nyct_gtfs_cpp

class RepeatedFieldIterator:
    def __init__(self, repeated_field):
        self.idx = 0
        self.repeated_field = repeated_field

    def __iter__(self):
        return self

    def __next__(self):
        self.idx += 1
        try:
            return self.repeated_field[self.idx - 1]
        except IndexError:
            self.idx = 0
            raise StopIteration


class RepeatedField:
    def __init__(self, message_ptr, field_name, attr_type, ext = -1):
        self._message_ptr = message_ptr
        self._field_name = field_name
        self._attr_type = attr_type
        self._ext = ext
        self._len = nyct_gtfs_cpp.get_size(self._message_ptr, self._field_name)

    def __len__(self):
        return self._len

    def __iter__(self):
        return RepeatedFieldIterator(self)

    def __getitem__(self, index):
        if index >= self._len:
            raise IndexError("RepeatedField index out of range")

        func = None
        if self._attr_type.name in {"UINT64", "UINT32", "BOOL", "ENUM"}:
            func = nyct_gtfs_cpp.get_repeated_uint_bool_enum
        elif self._attr_type.name in {"INT64", "INT32"}:
            func = nyct_gtfs_cpp.get_repeated_int
        elif self._attr_type.name in {"DOUBLE", "FLOAT"}:
            func = nyct_gtfs_cpp.get_repeated_double
        elif self._attr_type.name == "STRING":
            func = nyct_gtfs_cpp.get_repeated_string
        elif self._attr_type.name == "MESSAGE":
            func = nyct_gtfs_cpp.get_repeated_message

        if func is None:
            raise TypeError(f"Cpp layer returned unexpected type for object {self._field_name} at index {index}")

        if self._ext == -1:
            raw_result = func(self._message_ptr, self._field_name, index)
        else:
            raw_result = func(self._message_ptr, "", index, self._ext)

        if self._attr_type.name == "MESSAGE":
            return ProxyMessage(raw_result)
        return raw_result


class ProxyMessage:
    def __init__(self, message_ptr, is_ext=False):
        self._message_ptr = message_ptr
        self._is_ext = is_ext

    def __getitem__(self, ext):
        ext_id = ext.number
        if not self._is_ext:
            raise ValueError("Bracket syntax is only available on messages if they are tagged as Extension objects")

        attr_type = nyct_gtfs_cpp.get_type(self._message_ptr, "", ext_id)
        if attr_type.value == 0:
            raise AttributeError(f"No extension {ext_id}")

        if nyct_gtfs_cpp.is_repeated(self._message_ptr, "", ext_id):
            return RepeatedField(self._message_ptr, "", attr_type, ext_id)

        func = None
        if attr_type.name in {"UINT64", "UINT32", "BOOL", "ENUM"}:
            func = nyct_gtfs_cpp.get_uint_bool_enum
        elif attr_type.name in {"INT64", "INT32"}:
            func = nyct_gtfs_cpp.get_int
        elif attr_type.name in {"DOUBLE", "FLOAT"}:
            func = nyct_gtfs_cpp.get_double
        elif attr_type.name == "STRING":
            func = nyct_gtfs_cpp.get_string
        elif attr_type.name == "MESSAGE":
            func = nyct_gtfs_cpp.get_message

        if func is None:
            raise TypeError(f"Cpp layer returned unexpected type for extension {ext_id}")

        raw_result = func(self._message_ptr, "", ext_id)
        if attr_type.name == "MESSAGE":
            return ProxyMessage(raw_result)
        else:
            return raw_result

    def __getattr__(self, name):
        attr_type = nyct_gtfs_cpp.get_type(self._message_ptr, name)
        if attr_type.value == 0:
            raise AttributeError(f"No attribute {name}")

        if nyct_gtfs_cpp.is_repeated(self._message_ptr, name):
            return RepeatedField(self._message_ptr, name, attr_type)

        func = None
        if attr_type.name in {"UINT64", "UINT32", "BOOL", "ENUM"}:
            func = nyct_gtfs_cpp.get_uint_bool_enum
        elif attr_type.name in {"INT64", "INT32"}:
            func = nyct_gtfs_cpp.get_int
        elif attr_type.name in {"DOUBLE", "FLOAT"}:
            func = nyct_gtfs_cpp.get_double
        elif attr_type.name == "STRING":
            func = nyct_gtfs_cpp.get_string
        elif attr_type.name == "MESSAGE":
            func = nyct_gtfs_cpp.get_message

        if func is None:
            raise TypeError(f"Cpp layer returned unexpected type for object {name}")

        raw_result = func(self._message_ptr, name)
        if attr_type.name == "MESSAGE":
            return ProxyMessage(raw_result)
        else:
            return raw_result

    def HasField(self, name):
        return nyct_gtfs_cpp.has_field(self._message_ptr, name)

    @property
    def Extensions(self):
        return ProxyMessage(self._message_ptr, True)


class FeedMessage(ProxyMessage):
    def __init__(self, binary_data):
        feed_ptr = nyct_gtfs_cpp.get_feed(binary_data)
        super().__init__(feed_ptr)





