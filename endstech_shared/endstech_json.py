import json
import datetime
import uuid
import pytz
from dateutil.tz import tzutc


class EndstechEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None:
            return None

        if hasattr(obj, "tzinfo"):
            # This is here for a weird bug that was happening
            if obj.tzinfo == tzutc:
                tzinfo = "UTC"
            elif isinstance(obj.tzinfo, datetime.timezone):
                if obj.tzinfo.tzname(None) in ["+0000", "UTC"]:
                    tzinfo = "UTC"
                else:
                    raise Exception("Fixed offset is not utc, we need to figure out how to solve this issue.")
            else:
                tzinfo = str(obj.tzinfo)
        else:
            tzinfo = "UTC"

        if isinstance(obj, datetime.datetime):
            return {
                "__type__": "datetime",
                "year": obj.year,
                "month": obj.month,
                "day": obj.day,
                "hour": obj.hour,
                "minute": obj.minute,
                "second": obj.second,
                "microsecond": obj.microsecond,
                "tzinfo": tzinfo
            }
        elif isinstance(obj, datetime.date):
            return {
                "__type__": "date",
                "year": obj.year,
                "month": obj.month,
                "day": obj.day
            }
        elif isinstance(obj, datetime.time):
            return {
                "__type__": "time",
                "hour": obj.hour,
                "minute": obj.minute,
                "second": obj.second,
                "microsecond": obj.microsecond,
                "tzinfo": tzinfo
            }
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        else:
            return super(EndstechEncoder, self).default(obj)


class EndstechDecoder(json.JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.decode_special_types)

    def decode_special_types(self, dictionary):
        if "__type__" not in dictionary:
            return dictionary

        type_name = dictionary.pop("__type__")

        if "tzinfo" in dictionary:
            # This is here for a weird bug that was happening
            if dictionary["tzinfo"] is None or dictionary["tzinfo"] in ["None", "tzlocal()", "tzutc()"]:
                dictionary["tzinfo"] = "UTC"
            else:
                if type_name == "datetime":
                    tzinfo_to_localize = pytz.timezone(dictionary["tzinfo"])
                    dictionary.pop('tzinfo')
                    localized_datetime = tzinfo_to_localize.localize(datetime.datetime(**dictionary))
                    return localized_datetime

            dictionary["tzinfo"] = pytz.timezone(dictionary["tzinfo"])

        if type_name == "datetime":
            return datetime.datetime(**dictionary)
        elif type_name == "date":
            return datetime.date(**dictionary)
        elif type_name == "time":
            return datetime.time(**dictionary)
        elif type_name == "uuid":
            return uuid.UUID(**dictionary)
        else:
            dictionary["__type__"] = type_name
            return dictionary


class EndstechSerializer:
    def dumps(self, obj):
        return json.dumps(obj, cls=EndstechEncoder, separators=(",", ":")).encode("utf-8")

    def loads(self, string):
        return json.loads(string.decode("utf-8"), cls=EndstechDecoder)


def dumps(obj, **kwargs):
    return json.dumps(obj, cls=EndstechEncoder, **kwargs)


def dump(obj, file_pointer, **kwargs):
    return json.dump(obj, file_pointer, cls=EndstechEncoder, **kwargs)


def loads(string, **kwargs):
    return json.loads(string, cls=EndstechDecoder, **kwargs)


def load(file_pointer, **kwargs):
    return json.load(file_pointer, cls=EndstechDecoder, **kwargs)