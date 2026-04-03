class InteractionMode:
    def __init__(self, dm):
        self._dm = dm

    async def run(self):
        raise NotImplementedError
