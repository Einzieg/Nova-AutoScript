from device_operation.SQLiteClient import SQLiteClient


class Module:

    def __init__(self, module_name):
        self.db = SQLiteClient()
        self.module = self.db.fetch_one(f'SELECT * FROM module WHERE name = "{module_name}"')
        if self.module:
            self.id = self.module['id']
            self.name = self.module['name']
            self.port = self.module['port']
            self.stop_time = self.module['stop_time']
            if self.module['attack_fleet']:
                self.attack_fleet = self.module['attack_fleet']


if __name__ == '__main__':
    db = SQLiteClient()
    module = db.fetch_one('SELECT attack_fleet FROM module WHERE name = ?', ('Einzieg', ))['attack_fleet']
    print(module)
