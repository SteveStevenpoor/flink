################################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
from typing import Union

from pyflink import add_version_doc
from pyflink.java_gateway import get_gateway
from pyflink.table.expression import Expression, _get_java_expression, TimePointUnit, JsonOnNull
from pyflink.table.types import _to_java_data_type, DataType
from pyflink.table.udf import UserDefinedFunctionWrapper
from pyflink.util.api_stability_decorators import PublicEvolving
from pyflink.util.java_utils import to_jarray, load_java_class

__all__ = ['if_then_else', 'lit', 'col', 'range_', 'and_', 'or_', 'not_', 'UNBOUNDED_ROW',
           'UNBOUNDED_RANGE', 'CURRENT_ROW', 'CURRENT_RANGE', 'current_database',
           'current_date', 'current_time', 'current_timestamp',
           'current_watermark', 'local_time', 'local_timestamp',
           'temporal_overlaps', 'date_format', 'timestamp_diff', 'array', 'row', 'map_',
           'row_interval', 'pi', 'e', 'rand', 'rand_integer', 'atan2', 'negative', 'concat',
           'concat_ws', 'uuid', 'null_of', 'log', 'with_columns', 'without_columns', 'json',
           'json_string', 'json_object', 'json_object_agg', 'json_array', 'json_array_agg',
           'call', 'call_sql', 'source_watermark', 'to_timestamp_ltz', 'from_unixtime', 'to_date',
           'to_timestamp', 'convert_tz', 'unix_timestamp']


def _leaf_op(op_name: str) -> Expression:
    gateway = get_gateway()
    return Expression(getattr(gateway.jvm.Expressions, op_name)())


def _unary_op(op_name: str, arg) -> Expression:
    gateway = get_gateway()
    return Expression(getattr(gateway.jvm.Expressions, op_name)(_get_java_expression(arg)))


def _binary_op(op_name: str, first, second) -> Expression:
    gateway = get_gateway()
    return Expression(getattr(gateway.jvm.Expressions, op_name)(
        _get_java_expression(first),
        _get_java_expression(second)))


def _ternary_op(op_name: str, first, second, third) -> Expression:
    gateway = get_gateway()
    return Expression(getattr(gateway.jvm.Expressions, op_name)(
        _get_java_expression(first),
        _get_java_expression(second),
        _get_java_expression(third)))


def _quaternion_op(op_name: str, first, second, third, forth) -> Expression:
    gateway = get_gateway()
    return Expression(getattr(gateway.jvm.Expressions, op_name)(
        _get_java_expression(first),
        _get_java_expression(second),
        _get_java_expression(third),
        _get_java_expression(forth)))


def _varargs_op(op_name: str, *args):
    gateway = get_gateway()
    return Expression(
        getattr(gateway.jvm.Expressions, op_name)(*[_get_java_expression(arg) for arg in args]))


def _add_version_doc():
    from inspect import getmembers, isfunction
    from pyflink.table import expressions
    for o in getmembers(expressions):
        if isfunction(o[1]) and not o[0].startswith('_'):
            add_version_doc(o[1], "1.12.0")


@PublicEvolving()
def col(name: str) -> Expression:
    """
    Creates an expression which refers to a table's column.

    Example:
    ::

        >>> tab.select(col("key"), col("value"))

    :param name: the field name to refer to

    .. seealso:: :func:`~pyflink.table.expressions.with_all_columns`
    """
    return _unary_op("col", name)


@PublicEvolving()
def lit(v, data_type: DataType = None) -> Expression:
    """
    Creates a SQL literal.

    The data type is derived from the object's class and its value. For example, `lit(12)` leads
    to `INT`, `lit("abc")` leads to `CHAR(3)`.

    Example:
    ::

        >>> tab.select(col("key"), lit("abc"))
    """
    if data_type is None:
        return _unary_op("lit", v)
    else:
        return _binary_op("lit", v, _to_java_data_type(data_type))


@PublicEvolving()
def range_(start: Union[str, int], end: Union[str, int]) -> Expression:
    """
    Indicates a range from 'start' to 'end', which can be used in columns selection.

    Example:
    ::

        >>> tab.select(with_columns(range_('b', 'c')))

    .. seealso:: :func:`~pyflink.table.expressions.with_columns`
    """
    return _binary_op("range", start, end)


@PublicEvolving()
def and_(predicate0: Union[bool, Expression[bool]],
         predicate1: Union[bool, Expression[bool]],
         *predicates: Union[bool, Expression[bool]]) -> Expression[bool]:
    """
    Boolean AND in three-valued logic.
    """
    gateway = get_gateway()
    predicates = to_jarray(gateway.jvm.Object, [_get_java_expression(p) for p in predicates])
    return _ternary_op("and", predicate0, predicate1, predicates)


@PublicEvolving()
def or_(predicate0: Union[bool, Expression[bool]],
        predicate1: Union[bool, Expression[bool]],
        *predicates: Union[bool, Expression[bool]]) -> Expression[bool]:
    """
    Boolean OR in three-valued logic.
    """
    gateway = get_gateway()
    predicates = to_jarray(gateway.jvm.Object, [_get_java_expression(p) for p in predicates])
    return _ternary_op("or", predicate0, predicate1, predicates)


@PublicEvolving()
def not_(expression: Expression[bool]) -> Expression[bool]:
    """
    Inverts a given boolean expression.

    This method supports a three-valued logic by preserving `NULL`. This means if the input
    expression is `NULL`, the result will also be `NULL`.

    The resulting type is nullable if and only if the input type is nullable.

    Examples:
    ::

        >>> not_(lit(True)) # False
        >>> not_(lit(False)) # True
        >>> not_(lit(None, DataTypes.BOOLEAN())) # None
    """
    return _unary_op("not", expression)


"""
Offset constant to be used in the `preceding` clause of unbounded
:class:`~pyflink.table.window.Over`. Use this constant for a time interval.
Unbounded over windows start with the first row of a partition.

.. versionadded:: 1.12.0
"""
UNBOUNDED_ROW: Expression = Expression("UNBOUNDED_ROW")


"""
Offset constant to be used in the `preceding` clause of unbounded
:class:`~pyflink.table.window.Over` windows. Use this constant for a row-count interval.
Unbounded over windows start with the first row of a partition.

.. versionadded:: 1.12.0
"""
UNBOUNDED_RANGE: Expression = Expression("UNBOUNDED_RANGE")


"""
Offset constant to be used in the `following` clause of :class:`~pyflink.table.window.Over` windows.
Use this for setting the upper bound of the window to the current row.

.. versionadded:: 1.12.0
"""
CURRENT_ROW: Expression = Expression("CURRENT_ROW")


"""
Offset constant to be used in the `following` clause of :class:`~pyflink.table.window.Over` windows.
Use this for setting the upper bound of the window to the sort key of the current row, i.e.,
all rows with the same sort key as the current row are included in the window.

.. versionadded:: 1.12.0
"""
CURRENT_RANGE: Expression = Expression("CURRENT_RANGE")


@PublicEvolving()
def current_database() -> Expression:
    """
    Returns the current database
    """
    return _leaf_op("currentDatabase")


@PublicEvolving()
def current_date() -> Expression:
    """
    Returns the current SQL date in local time zone.
    """
    return _leaf_op("currentDate")


@PublicEvolving()
def current_time() -> Expression:
    """
    Returns the current SQL time in local time zone.
    """
    return _leaf_op("currentTime")


@PublicEvolving()
def current_timestamp() -> Expression:
    """
    Returns the current SQL timestamp in local time zone,
    the return type of this expression is TIMESTAMP_LTZ.
    """
    return _leaf_op("currentTimestamp")


@PublicEvolving()
def current_watermark(rowtimeAttribute) -> Expression:
    """
    Returns the current watermark for the given rowtime attribute, or NULL if no common watermark of
    all upstream operations is available at the current operation in the pipeline.

    The function returns the watermark with the same type as the rowtime attribute, but with an
    adjusted precision of 3. For example, if the rowtime attribute is `TIMESTAMP_LTZ(9)`, the
    function will return `TIMESTAMP_LTZ(3)`.

    If no watermark has been emitted yet, the function will return `NULL`. Users must take care of
    this when comparing against it, e.g. in order to filter out late data you can use

    ::

        WHERE CURRENT_WATERMARK(ts) IS NULL OR ts > CURRENT_WATERMARK(ts)
    """
    return _unary_op("currentWatermark", rowtimeAttribute)


@PublicEvolving()
def local_time() -> Expression:
    """
    Returns the current SQL time in local time zone.
    """
    return _leaf_op("localTime")


@PublicEvolving()
def local_timestamp() -> Expression:
    """
    Returns the current SQL timestamp in local time zone,
    the return type of this expression s TIMESTAMP.
    """
    return _leaf_op("localTimestamp")


@PublicEvolving()
def to_date(date_str: Union[str, Expression[str]],
            format: Union[str, Expression[str]] = None) -> Expression:
    """
    Converts the date string with the given format (by default 'yyyy-MM-dd') to a date.

    :param date_str: The date string
    :param format: The format of the string
    :return: The date value with DATE type.
    """
    if format is None:
        return _unary_op("toDate", date_str)
    else:
        return _binary_op("toDate", date_str, format)


@PublicEvolving()
def to_timestamp(timestamp_str: Union[str, Expression[str]],
                 format: Union[str, Expression[str]] = None) -> Expression:
    """
    Converts the date time string with the given format (by default: 'yyyy-MM-dd HH:mm:ss')
    under the 'UTC+0' time zone to a timestamp.

    :param timestamp_str: The date time string
    :param format: The format of the string
    :return: The date value with TIMESTAMP type.
    """
    if format is None:
        return _unary_op("toTimestamp", timestamp_str)
    else:
        return _binary_op("toTimestamp", timestamp_str, format)


@PublicEvolving()
def to_timestamp_ltz(*args) -> Expression:
    """
    Converts a value to a timestamp with local time zone.

    Supported functions:
    1. to_timestamp_ltz(Numeric) -> DataTypes.TIMESTAMP_LTZ
    Converts a numeric value of epoch milliseconds to a TIMESTAMP_LTZ. The default precision is 3.
    2. to_timestamp_ltz(Numeric, Integer) -> DataTypes.TIMESTAMP_LTZ
    Converts a numeric value of epoch seconds or epoch milliseconds to a TIMESTAMP_LTZ.
    Valid precisions are 0 or 3.
    3. to_timestamp_ltz(String) -> DataTypes.TIMESTAMP_LTZ
    Converts a timestamp string using default format 'yyyy-MM-dd HH:mm:ss.SSS' to a TIMESTAMP_LTZ.
    4. to_timestamp_ltz(String, String) -> DataTypes.TIMESTAMP_LTZ
    Converts a timestamp string using format (default 'yyyy-MM-dd HH:mm:ss.SSS') to a TIMESTAMP_LTZ.
    5. to_timestamp_ltz(String, String, String) -> DataTypes.TIMESTAMP_LTZ
    Converts a timestamp string string1 using format string2 (default 'yyyy-MM-dd HH:mm:ss.SSS')
    in time zone string3 (default 'UTC') to a TIMESTAMP_LTZ.
    Supports any timezone that is available in Java's TimeZone database.

    Example:
    ::

        >>> table.select(to_timestamp_ltz(100))  # numeric with default precision
        >>> table.select(to_timestamp_ltz(100, 0))  # numeric with second precision
        >>> table.select(to_timestamp_ltz(100, 3))  # numeric with millisecond precision
        >>> table.select(to_timestamp_ltz("2023-01-01 00:00:00"))  # string with default format
        >>> table.select(to_timestamp_ltz("01/01/2023", "MM/dd/yyyy"))  # string with format
        >>> table.select(to_timestamp_ltz("2023-01-01 00:00:00",
                                        "yyyy-MM-dd HH:mm:ss",
                                        "UTC"))  # string with format and timezone
    """
    if len(args) == 1:
        return _unary_op("toTimestampLtz", lit(args[0]))

    # For two arguments case (numeric + precision or string + format)
    elif len(args) == 2:
        return _binary_op("toTimestampLtz", lit(args[0]), lit(args[1]))

    # For three arguments case (string + format + timezone)
    else:
        return _ternary_op("toTimestampLtz", lit(args[0]), lit(args[1]), lit(args[2]))


@PublicEvolving()
def temporal_overlaps(left_time_point,
                      left_temporal,
                      right_time_point,
                      right_temporal) -> Expression:
    """
    Determines whether two anchored time intervals overlap. Time point and temporal are
    transformed into a range defined by two time points (start, end). The function
    evaluates `left_end >= right_start && right_end >= left_start`.

    e.g.
        temporal_overlaps(
            lit("2:55:00").to_time,
            lit(1).hours,
            lit("3:30:00").to_time,
            lit(2).hours) leads to true.

    :param left_time_point: The left time point
    :param left_temporal: The time interval from the left time point
    :param right_time_point: The right time point
    :param right_temporal: The time interval from the right time point
    :return: An expression which indicates whether two anchored time intervals overlap.
    """
    return _quaternion_op("temporalOverlaps",
                          left_time_point, left_temporal, right_time_point, right_temporal)


@PublicEvolving()
def date_format(timestamp, format) -> Expression:
    """
    Formats a timestamp as a string using a specified format.
    The format must be compatible with MySQL's date formatting syntax as used by the
    date_parse function.

    For example `date_format(col("time"), "%Y, %d %M")` results in strings formatted as
    "2017, 05 May".

    :param timestamp: The timestamp to format as string.
    :param format: The format of the string.
    :return: The formatted timestamp as string.
    """
    return _binary_op("dateFormat", timestamp, format)


@PublicEvolving()
def timestamp_diff(time_point_unit: TimePointUnit, time_point1, time_point2) -> Expression:
    """
    Returns the (signed) number of :class:`~pyflink.table.expression.TimePointUnit` between
    time_point1 and time_point2.

    For example,
    `timestamp_diff(TimePointUnit.DAY, lit("2016-06-15").to_date, lit("2016-06-18").to_date`
    leads to 3.

    :param time_point_unit: The unit to compute diff.
    :param time_point1: The first point in time.
    :param time_point2: The second point in time.
    :return: The number of intervals as integer value.
    """
    return _ternary_op("timestampDiff", time_point_unit._to_j_time_point_unit(),
                       time_point1, time_point2)


@PublicEvolving()
def convert_tz(date_str: Union[str, Expression[str]],
               tz_from: Union[str, Expression[str]],
               tz_to: Union[str, Expression[str]]) -> Expression:
    """
    Converts a datetime string date_str (with default ISO timestamp format 'yyyy-MM-dd HH:mm:ss')
    from time zone tz_from to time zone tz_to. The format of time zone should be either an
    abbreviation such as "PST", a full name such as "America/Los_Angeles", or a custom ID such as
    "GMT-08:00". E.g., convert_tz('1970-01-01 00:00:00', 'UTC', 'America/Los_Angeles') returns
    '1969-12-31 16:00:00'.

    Example:
    ::

        >>> tab.select(convert_tz(col('a'), 'PST', 'UTC'))

    :param date_str: the date time string
    :param tz_from: the original time zone
    :param tz_to: the target time zone
    :return: The formatted timestamp as string.
    """
    return _ternary_op("convertTz", date_str, tz_from, tz_to)


@PublicEvolving()
def from_unixtime(unixtime, format=None) -> Expression:
    """
    Converts unix timestamp (seconds since '1970-01-01 00:00:00' UTC) to datetime string the given
    format. The default format is "yyyy-MM-dd HH:mm:ss".
    """
    if format is None:
        return _unary_op("fromUnixtime", unixtime)
    else:
        return _binary_op("fromUnixtime", unixtime, format)


@PublicEvolving()
def unix_timestamp(date_str: Union[str, Expression[str]] = None,
                   format: Union[str, Expression[str]] = None) -> Expression:
    """
    Gets the current unix timestamp in seconds if no arguments are not specified.
    This function is not deterministic which means the value would be recalculated for each record.

    If the date time string date_str is specified, it will convert the given date time string
    in the specified format (by default: yyyy-MM-dd HH:mm:ss if not specified) to unix timestamp
    (in seconds), using the specified timezone in table config.
    """

    if date_str is None:
        return _leaf_op("unixTimestamp")
    elif format is None:
        return _unary_op("unixTimestamp", date_str)
    else:
        return _binary_op("unixTimestamp", date_str, format)


@PublicEvolving()
def array(head, *tail) -> Expression:
    """
    Creates an array of literals.

    Example:
    ::

        >>> tab.select(array(1, 2, 3))
    """
    gateway = get_gateway()
    tail = to_jarray(gateway.jvm.Object, [_get_java_expression(t) for t in tail])
    return _binary_op("array", head, tail)


@PublicEvolving()
def row(head, *tail) -> Expression:
    """
    Creates a row of expressions.

    Example:
    ::

        >>> tab.select(row("key1", 1))
    """
    gateway = get_gateway()
    tail = to_jarray(gateway.jvm.Object, [_get_java_expression(t) for t in tail])
    return _binary_op("row", head, tail)


@PublicEvolving()
def map_(key, value, *tail) -> Expression:
    """
    Creates a map of expressions.

    Example:
    ::

        >>> tab.select(
        >>>     map_(
        >>>         "key1", 1,
        >>>         "key2", 2,
        >>>         "key3", 3
        >>>     ))

    .. note::

        keys and values should have the same types for all entries.
    """
    gateway = get_gateway()
    tail = to_jarray(gateway.jvm.Object, [_get_java_expression(t) for t in tail])
    return _ternary_op("map", key, value, tail)


@PublicEvolving()
def map_from_arrays(key, value) -> Expression:
    """
    Creates a map from an array of keys and an array of values.

    Example:
    ::

        >>> tab.select(
        >>>     map_from_arrays(
        >>>         array("key1", "key2", "key3"),
        >>>         array(1, 2, 3)
        >>>     ))

    .. note::

        both arrays should have the same length.
    """
    return _binary_op("mapFromArrays", key, value)


@PublicEvolving()
def object_of(class_name: str, *args) -> Expression:
    """
    Creates a structured object from a list of key-value pairs.

    This function creates an instance of a structured type identified by the given class name.
    The structured type is created by providing alternating key-value pairs where keys must be
    string literals and values can be arbitrary expressions.

    Note: The class name is only used for distinguishing two structured types with identical fields.
    Structured types are internally handled with suitable data structures.
    Thus, serialization and equality checks are managed by the system.

    In Table API and UDF calls, the system will attempt to resolve
    the class name to an actual implementation class.
    In this case the class name needs to be present in the user classpath.
    If resolution fails, Row class is used as a fallback.

    Examples:
    ::

        >>> # Creates a User object with name="Alice" and age=30
        >>> object_of("com.example.User", "name", "Alice", "age", 30)

    :param class_name: The fully qualified class name
    :param args: Alternating key-value pairs: key1, value1, key2, value2, ...
    :return: A structured object expression

    .. seealso:: SQL function: OBJECT_OF('com.example.User', 'name', 'Bob', 'age', 25)
    """
    return _varargs_op("objectOf", class_name, *args)


@PublicEvolving()
def row_interval(rows: int) -> Expression:
    """
    Creates an interval of rows.

    Example:
    ::

        >>> tab.window(Over
        >>>         .partition_by(col('a'))
        >>>         .order_by(col('proctime'))
        >>>         .preceding(row_interval(4))
        >>>         .following(CURRENT_ROW)
        >>>         .alias('w'))

    :param rows: the number of rows
    """
    return _unary_op("rowInterval", rows)


@PublicEvolving()
def pi() -> Expression[float]:
    """
    Returns a value that is closer than any other value to `pi`.
    """
    return _leaf_op("pi")


@PublicEvolving()
def e() -> Expression[float]:
    """
    Returns a value that is closer than any other value to `e`.
    """
    return _leaf_op("e")


@PublicEvolving()
def rand(seed: Union[int, Expression[int]] = None) -> Expression[float]:
    """
    Returns a pseudorandom double value between 0.0 (inclusive) and 1.0 (exclusive) with a
    initial seed if specified. Two rand() functions will return identical sequences of numbers if
    they have same initial seed.
    """
    if seed is None:
        return _leaf_op("rand")
    else:
        return _unary_op("rand", seed)


@PublicEvolving()
def rand_integer(bound: Union[int, Expression[int]],
                 seed: Union[int, Expression[int]] = None) -> Expression:
    """
    Returns a pseudorandom integer value between 0 (inclusive) and the specified value
    (exclusive) with a initial seed if specified. Two rand_integer() functions will return
    identical sequences of numbers if they have same initial seed and same bound.
    """
    if seed is None:
        return _unary_op("randInteger", bound)
    else:
        return _binary_op("randInteger", seed, bound)


@PublicEvolving()
def atan2(y, x) -> Expression[float]:
    """
    Calculates the arc tangent of a given coordinate.
    """
    return _binary_op("atan2", y, x)


@PublicEvolving()
def negative(v) -> Expression:
    """
    Returns negative numeric.
    """
    return _unary_op("negative", v)


@PublicEvolving()
def concat(first: Union[str, Expression[str]],
           *others: Union[str, Expression[str]]) -> Expression[str]:
    """
    Returns the string that results from concatenating the arguments.
    Returns NULL if any argument is NULL.
    """
    gateway = get_gateway()
    return _binary_op("concat",
                      first,
                      to_jarray(gateway.jvm.Object,
                                [_get_java_expression(other) for other in others]))


@PublicEvolving()
def concat_ws(separator: Union[str, Expression[str]],
              first: Union[str, Expression[str]],
              *others: Union[str, Expression[str]]) -> Expression[str]:
    """
    Returns the string that results from concatenating the arguments and separator.
    Returns NULL If the separator is NULL.

    .. note::

        this function does not skip empty strings. However, it does skip any NULL
        values after the separator argument.
    """
    gateway = get_gateway()
    return _ternary_op("concatWs",
                       separator,
                       first,
                       to_jarray(gateway.jvm.Object,
                                 [_get_java_expression(other) for other in others]))


@PublicEvolving()
def uuid() -> Expression[str]:
    """
    Returns an UUID (Universally Unique Identifier) string (e.g.,
    "3d3c68f7-f608-473f-b60c-b0c44ad4cc4e") according to RFC 4122 type 4 (pseudo randomly
    generated) UUID. The UUID is generated using a cryptographically strong pseudo random number
    generator.
    """
    return _leaf_op("uuid")


@PublicEvolving()
def null_of(data_type: DataType) -> Expression:
    """
    Returns a null literal value of a given data type.
    """
    return _unary_op("nullOf", _to_java_data_type(data_type))


@PublicEvolving()
def log(v, base=None) -> Expression[float]:
    """
    If base is specified, calculates the logarithm of the given value to the given base.
    Otherwise, calculates the natural logarithm of the given value.
    """
    if base is None:
        return _unary_op("log", v)
    else:
        return _binary_op("log", base, v)


@PublicEvolving()
def source_watermark() -> Expression:
    """
    Source watermark declaration for schema.

    This is a marker function that doesn't have concrete runtime implementation. It can only
    be used as a single expression for watermark strategies in schema declarations. The declaration
    will be pushed down into a table source that implements the `SupportsSourceWatermark`
    interface. The source will emit system-defined watermarks afterwards.

    Please check the documentation whether the connector supports source watermarks.
    """
    return _leaf_op("sourceWatermark")


@PublicEvolving()
def if_then_else(condition: Union[bool, Expression[bool]], if_true, if_false) -> Expression:
    """
    Ternary conditional operator that decides which of two other expressions should be evaluated
    based on a evaluated boolean condition.

    e.g. if_then_else(col("f0") > 5, "A", "B") leads to "A"

    :param condition: condition boolean condition
    :param if_true: expression to be evaluated if condition holds
    :param if_false: expression to be evaluated if condition does not hold
    """
    return _ternary_op("ifThenElse", condition, if_true, if_false)


@PublicEvolving()
def coalesce(*args) -> Expression:
    """
    Returns the first argument that is not NULL.

    If all arguments are NULL, it returns NULL as well.
    The return type is the least restrictive, common type of all of its arguments.
    The return type is nullable if all arguments are nullable as well.

    Examples:
    ::

        >>> coalesce(None, "default") # Returns "default"
        >>> # Returns the first non-null value among f0 and f1,
        >>> # or "default" if f0 and f1 are both null
        >>> coalesce(col("f0"), col("f1"), "default")

    :param args: the input expressions.
    """
    gateway = get_gateway()
    args = to_jarray(gateway.jvm.Object, [_get_java_expression(arg) for arg in args])
    return _unary_op("coalesce", args)


@PublicEvolving()
def with_all_columns() -> Expression:
    """
    Creates an expression that selects all columns. It can be used wherever an array of
    expression is accepted such as function calls, projections, or groupings.

    This expression is a synonym of col("*"). It is semantically equal to SELECT * in
    SQL when used in a projection.

    e.g. tab.select(with_all_columns())

    .. seealso:: :func:`~pyflink.table.expressions.with_columns`
                 :func:`~pyflink.table.expressions.without_columns`
    """
    return _leaf_op("withAllColumns")


@PublicEvolving()
def with_columns(head, *tails) -> Expression:
    """
    Creates an expression that selects a range of columns. It can be used wherever an array of
    expression is accepted such as function calls, projections, or groupings.

    A range can either be index-based or name-based. Indices start at 1 and boundaries are
    inclusive.

    e.g. with_columns(range_("b", "c")) or with_columns(col("*"))

    .. seealso:: :func:`~pyflink.table.expressions.range_`,
                 :func:`~pyflink.table.expressions.without_columns`
    """
    gateway = get_gateway()
    tails = to_jarray(gateway.jvm.Object, [_get_java_expression(t) for t in tails])
    return _binary_op("withColumns", head, tails)


@PublicEvolving()
def without_columns(head, *tails) -> Expression:
    """
    Creates an expression that selects all columns except for the given range of columns. It can
    be used wherever an array of expression is accepted such as function calls, projections, or
    groupings.

    A range can either be index-based or name-based. Indices start at 1 and boundaries are
    inclusive.

    e.g. without_columns(range_("b", "c")) or without_columns(col("c"))

    .. seealso:: :func:`~pyflink.table.expressions.range_`,
                 :func:`~pyflink.table.expressions.with_columns`
    """
    gateway = get_gateway()
    tails = to_jarray(gateway.jvm.Object, [_get_java_expression(t) for t in tails])
    return _binary_op("withoutColumns", head, tails)


@PublicEvolving()
def json(value) -> Expression:
    """
    Expects a raw, pre-formatted JSON string and returns its values as-is without escaping
    it as a string.

    This function can currently only be used within the `JSON_OBJECT` and `JSON_ARRAY` functions.
    It allows passing pre-formatted JSON strings that will be inserted directly into the
    resulting JSON structure rather than being escaped as a string value. This allows storing
    nested JSON structures in a `JSON_OBJECT` or `JSON_ARRAY` without processing them as strings,
    which is often useful when ingesting already formatted json data. If the value is NULL or
    empty, the function returns NULL.

    Examples:
    ::

        >>> # {"nested":{"value":42}}
        >>> json_object(JsonOnNull.NULL, "nested", json('{"value": 42}'))

        >>> # {"K": null}
        >>> json_object(JsonOnNull.NULL, "K", json(''))

        >>> # [{"nested":{"value":42}}]
        >>> json_array(JsonOnNull.NULL, json('{"nested":{"value": 42}}'))

        >>> # [null]
        >>> json_array(JsonOnNull.NULL, json(''))

        >>> # Invalid - JSON function can only be used within JSON_OBJECT
        >>> json('{"value": 42}')
    """
    return _unary_op("json", value)


@PublicEvolving()
def json_string(value) -> Expression:
    """
    Serializes a value into JSON.

    This function returns a JSON string containing the serialized value. If the value is `NULL`,
    the function returns `NULL`.

    Examples:
    ::

        >>> json_string(null_of(DataTypes.INT())) # None

        >>> json_string(1)               # '1'
        >>> json_string(True)            # 'true'
        >>> json_string("Hello, World!") # '"Hello, World!"'
        >>> json_string([1, 2])          # '[1,2]'
    """
    return _unary_op("jsonString", value)


@PublicEvolving()
def json_object(on_null: JsonOnNull = JsonOnNull.NULL, *args) -> Expression:
    """
    Builds a JSON object string from a list of key-value pairs.

    `args` is an even-numbered list of alternating key/value pairs. Note that keys must be
    non-`NULL` string literals, while values may be arbitrary expressions.

    This function returns a JSON string. The `on_null` behavior defines how to treat `NULL` values.

    Values which are created from another JSON construction function call (`json_object`,
    `json_array`) are inserted directly rather than as a string. This allows building nested JSON
    structures.

    Examples:
    ::

        >>> json_object() # '{}'
        >>> json_object(JsonOnNull.NULL, "K1", "V1", "K2", "V2") # '{"K1":"V1","K2":"V2"}'

        >>> # Expressions as values
        >>> json_object(JsonOnNull.NULL, "orderNo", col("orderId"))

        >>> json_object(JsonOnNull.NULL, "K1", null_of(DataTypes.STRING()))   # '{"K1":null}'
        >>> json_object(JsonOnNull.ABSENT, "K1", null_of(DataTypes.STRING())) # '{}'

        >>> # '{"K1":{"K2":"V"}}'
        >>> json_object(JsonOnNull.NULL, "K1", json('{"K2":"V"}'))

        >>> # '{"K1":{"K2":"V"}}'
        >>> json_object(JsonOnNull.NULL, "K1", json_object(JsonOnNull.NULL, "K2", "V"))

    .. seealso:: :func:`~pyflink.table.expressions.json`
    .. seealso:: :func:`~pyflink.table.expressions.json_array`
    """
    return _varargs_op("jsonObject", *(on_null._to_j_json_on_null(), *args))


@PublicEvolving()
def json_object_agg(on_null: JsonOnNull,
                    key_expr: Union[str, Expression[str]],
                    value_expr) -> Expression:
    """
    Builds a JSON object string by aggregating key-value expressions into a single JSON object.

    The key expression must return a non-nullable character string. Value expressions can be
    arbitrary, including other JSON functions. If a value is `NULL`, the `on_null` behavior defines
    what to do.

    Note that keys must be unique. If a key occurs multiple times, an error will be thrown.

    This function is currently not supported in `OVER` windows.

    Examples:
    ::

        >>> # '{"Apple":2,"Banana":17,"Orange":0}'
        >>> orders.select(json_object_agg(JsonOnNull.NULL, col("product"), col("cnt")))
    """
    return _ternary_op("jsonObjectAgg", on_null._to_j_json_on_null(), key_expr, value_expr)


@PublicEvolving()
def json_array(on_null: JsonOnNull = JsonOnNull.ABSENT, *args) -> Expression:
    """
    Builds a JSON array string from a list of values.

    This function returns a JSON string. The values can be arbitrary expressions. The `on_null`
    behavior defines how to treat `NULL` values.

    Elements which are created from another JSON construction function call (`json_object`,
    `json_array`) are inserted directly rather than as a string. This allows building nested JSON
    structures.

    Examples:
    ::

        >>> json_array() # '[]'
        >>> json_array(JsonOnNull.NULL, 1, "2") # '[1,"2"]'

        >>> # Expressions as values
        >>> json_array(JsonOnNull.NULL, col("orderId"))

        >>> json_array(JsonOnNull.NULL, null_of(DataTypes.STRING()))   # '[null]'
        >>> json_array(JsonOnNull.ABSENT, null_of(DataTypes.STRING())) # '[]'

        >>> json_array(JsonOnNull.NULL, json_array(JsonOnNull.NULL, 1)) # '[[1]]'

        # '[{"nested_json":{"value":42}}]'
        >>> json_array(JsonOnNull.NULL, json('{"nested_json": {"value": 42}}'))

    .. seealso:: :func:`~pyflink.table.expressions.json`
    .. seealso:: :func:`~pyflink.table.expressions.json_object`
    """
    return _varargs_op("jsonArray", *(on_null._to_j_json_on_null(), *args))


@PublicEvolving()
def json_array_agg(on_null: JsonOnNull, item_expr) -> Expression:
    """
    Builds a JSON object string by aggregating items into an array.

    Item expressions can be arbitrary, including other JSON functions. If a value is `NULL`, the
    `on_null` behavior defines what to do.

    This function is currently not supported in `OVER` windows, unbounded session windows, or hop
    windows.

    Examples:
    ::

        >>> # '["Apple","Banana","Orange"]'
        >>> orders.select(json_array_agg(JsonOnNull.NULL, col("product")))
    """
    return _binary_op("jsonArrayAgg", on_null._to_j_json_on_null(), item_expr)


@PublicEvolving()
def lag(expr, offset=1, default=None) -> Expression:
    """
    A window function that provides access to a row at a specified physical offset which comes
    before the current row.
    """
    if default is None:
        return _binary_op("lag", expr, offset)
    else:
        return _ternary_op("lag", expr, offset, default)


@PublicEvolving()
def lead(expr, offset=1, default=None) -> Expression:
    """
    A window function that provides access to a row at a specified physical offset which comes
    after the current row.
    """
    if default is None:
        return _binary_op("lead", expr, offset)
    else:
        return _ternary_op("lead", expr, offset, default)


@PublicEvolving()
def call(f: Union[str, UserDefinedFunctionWrapper], *args) -> Expression:
    """
    The first parameter `f` could be a str or a Python user-defined function.

    When it is str, this is a call to a function that will be looked up in a catalog. There
    are two kinds of functions:

        - System functions - which are identified with one part names
        - Catalog functions - which are identified always with three parts names
            (catalog, database, function)

    Moreover each function can either be a temporary function or permanent one
    (which is stored in an external catalog).

    Based on that two properties the resolution order for looking up a function based on
    the provided `function_name` is following:

        - Temporary system function
        - System function
        - Temporary catalog function
        - Catalog function

    :param f: the path of the function or the Python user-defined function.
    :param args: parameters of the user-defined function.
    """
    gateway = get_gateway()

    if isinstance(f, str):
        return Expression(gateway.jvm.Expressions.call(
            f, to_jarray(gateway.jvm.Object, [_get_java_expression(arg) for arg in args])))

    expressions_clz = load_java_class("org.apache.flink.table.api.Expressions")
    function_definition_clz = load_java_class('org.apache.flink.table.functions.FunctionDefinition')
    j_object_array_type = to_jarray(gateway.jvm.Object, []).getClass()

    api_call_method = expressions_clz.getDeclaredMethod(
        "apiCall",
        to_jarray(gateway.jvm.Class, [function_definition_clz, j_object_array_type]))
    api_call_method.setAccessible(True)

    return Expression(api_call_method.invoke(
        None,
        to_jarray(gateway.jvm.Object,
                  [f._java_user_defined_function(),
                   to_jarray(gateway.jvm.Object, [_get_java_expression(arg) for arg in args])])))


@PublicEvolving()
def call_sql(sql_expression: str) -> Expression:
    """
    A call to a SQL expression.

    The given string is parsed and translated into a Table API expression during planning. Only
    the translated expression is evaluated during runtime.

    Note: Currently, calls are limited to simple scalar expressions. Calls to aggregate or
    table-valued functions are not supported. Sub-queries are also not allowed.

    :param sql_expression: SQL expression to be translated
    """
    return _unary_op("callSql", sql_expression)


_add_version_doc()
