# Typing: Coroutine[YieldResult, SendArgument, ReturnType]
from typing import Coroutine

# An "awaitable" object is any one that defines the __await__ method.
# This method must return an iterable.
class SuspendAlways():
	def __await__(self):
		yield

# This function defines an async function but that does not internally call
# any other async functions.  This will cause a caller to not suspend when
# awaiting the result.
async def SuspendNever():
	print("SuspendNever (does not suspend when awaited)")

# Conditionally call SuspendAlways or SuspendNever based on an argument.
async def TestAsync(value):
	print(f"TestAsync-Enter, value={value}");
	if value == 'always':
		await SuspendAlways()
	elif value == 'never':
		await SuspendNever()
	else:
		raise Exception("Value must be always or never")
	print("TestAsync-Exit");

async def MainAsync():
	print("MainAsync-Enter")
	await TestAsync('always')
	await TestAsync('never')
	print("MainAsync-Exit")

def Step(coro: Coroutine):
	try:
		coro.send(None)
		return True
	except StopIteration:
		print("Stop iterating")
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
MainAsync-Enter
TestAsync-Enter, value=always
Stepping
TestAsync-Exit
TestAsync-Enter, value=never
SuspendNever (does not suspend when awaited)
TestAsync-Exit
MainAsync-Exit
Stop iterating
Done
"""
