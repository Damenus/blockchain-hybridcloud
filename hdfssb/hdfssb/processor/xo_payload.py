class XoPayload:

    def __init__(self, payload):
        try:
            # The payload is csv utf-8 encoded string
            name, action, space = payload.decode().split(",")
        except ValueError:
            raise InvalidTransaction("Invalid payload serialization")

        if not name:
            raise InvalidTransaction('Name is required')

        if '|' in name:
            raise InvalidTransaction('Name cannot contain "|"')

        if not action:
            raise InvalidTransaction('Action is required')

        if action not in ('create', 'take', 'delete'):
            raise InvalidTransaction('Invalid action: {}'.format(action))

        if action == 'take':
            try:

                if int(space) not in range(1, 10):
                    raise InvalidTransaction(
                        "Space must be an integer from 1 to 9")
            except ValueError:
                raise InvalidTransaction(
                    'Space must be an integer from 1 to 9')

        if action == 'take':
            space = int(space)

        self._name = name
        self._action = action
        self._space = space

    @staticmethod
    def from_bytes(payload):
        return XoPayload(payload=payload)

    @property
    def name(self):
        return self._name

    @property
    def action(self):
        return self._action

    @property
    def space(self):
        return self._space