# Python Event Loops

Python Event Loops

## References

* [Python Coroutine Docs (Library)](https://docs.python.org/3/library/asyncio-task.html)
* [Python Coroutine Docs (Reference)](https://docs.python.org/3/reference/datamodel.html#coroutine-objects)
* [Python Source Code](https://github.com/python/cpython)
* [UVLoop](https://github.com/MagicStack/uvloop)

## Notes

* The `asyncio.BaseEventLoop` makes it look like you can make your own and
  customize it, but it does not really.  Most of the inner workings of the
  `asyncio` library are non-public and some hidden by `__`.
* The `uvloop.Loop` implements all of the functions of the `asyncio.EventLoop`
  but it appears to be a completely custom implemenation that does not extend
  the existing type.  It does still use the underlying `asyncio.Task/Future`
  types though and hooks into the `asyncio._set_running_loop()` calls.

