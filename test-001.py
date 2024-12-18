# Typing: Coroutine[YieldResult, SendArgument, ReturnType]
from typing import Coroutine

# An "awaitable" object is any one that defines the __await__ method.
# This method must return an iterable.
class SuspendAlways():
	def __await__(self):
		yield

# This is just a test async function that prints enter/leave around an async
# call.
async def TestAsync():
	print("TestAsync-Enter");
	await SuspendAlways()
	print("TestAsync-Exit");

# Top Level async entrypoint
async def MainAsync():
	print("MainAsync-Enter")
	await TestAsync()
	await TestAsync()
	print("MainAsync-Exit")
	return 1

# Example function to "step" a coroutine.
# Returns true if the coroutine can still be stepped.
def Step(coro: Coroutine):
	try:
		# Display information about the coroutine
		# https://python.readthedocs.io/en/stable/library/inspect.html
		print(f"Name={coro.__name__} ({coro.__qualname__})")

		# Advance the coroutine by calling send
		result = coro.send(None)
		print(f"Result (of yield)={result}")

		# Diagnostics - we can technically inspect the item this coroutine
		# is currently awaiting.
		if coro.cr_await is not None:
			print(f"Currently awaiting={coro.cr_await}")

		# Return true we can still step
		return True
	# StopIteration is thrown from Coroutine send when the coroutine has
	# completed.  This indicates that no more stepping is required.
	except StopIteration as exception:
		# The exception contains the result of the function or None
		print(f"Stop iterating, value={exception.value}")
		return False

print("Entry point")
coro = MainAsync()
print("Created coroutine (has not started executing yet)")
while Step(coro):
	print("Stepping")
print("Done")

"""
Entry point
Created coroutine (has not started executing yet)
Name=MainAsync (MainAsync)
MainAsync-Enter
TestAsync-Enter
Result (of yield)=None
Currently awaiting=<coroutine object TestAsync at 0x000002449B6D68C0>
Stepping
Name=MainAsync (MainAsync)
TestAsync-Exit
TestAsync-Enter
Result (of yield)=None
Currently awaiting=<coroutine object TestAsync at 0x000002449B6D68C0>
Stepping
Name=MainAsync (MainAsync)
TestAsync-Exit
MainAsync-Exit
Stop iterating, value=1
Done
"""
