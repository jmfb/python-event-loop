import random

class SuspendAlways():
	def __await__(self):
		yield

async def SuspendNever():
	pass

async def SuspendMaybe():
	await random.choice([SuspendAlways, SuspendNever])()
