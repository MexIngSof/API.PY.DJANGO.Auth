import csv
from pathlib import Path

from django.apps import apps
from django.db import migrations
from django.test import SimpleTestCase


class PascalCasePhysicalColumnTests(SimpleTestCase):
    OWNER = "Auth"
    EXPECTED = 6

    def test_all_owner_candidates_have_pascalcase_physical_columns(self):
        manifest = Path(__file__).resolve().parent / "fixtures/PASCALCASE_MODEL_COLUMN_MAPPING.csv"
        models_by_table = {model._meta.db_table.replace('"', '').split(".")[-1]: model for model in apps.get_models(include_auto_created=True)}
        with manifest.open(encoding="utf-8-sig", newline="") as source:
            mappings = [row for row in csv.DictReader(source) if row["Database"] == self.OWNER]
        self.assertEqual(len(mappings), self.EXPECTED)
        mismatches = []
        for mapping in mappings:
            model = models_by_table.get(mapping["Table"])
            if model is None:
                mismatches.append(f"{mapping['Table']}.{mapping['OldColumn']}: model missing")
                continue
            try:
                field = model._meta.get_field(mapping["Field"])
            except Exception as error:
                mismatches.append(f"{mapping['Table']}.{mapping['Field']}: {error}")
                continue
            if field.column != mapping["NewColumn"]:
                mismatches.append(f"{mapping['Table']}.{mapping['OldColumn']}: actual={field.column}, expected={mapping['NewColumn']}")
        self.assertFalse(mismatches, "Physical column mismatches:\n" + "\n".join(mismatches[:20]))

    def test_auth_join_migration_declares_fields_and_reversible_column_renames(self):
        from importlib import import_module

        migration = import_module("user.migrations.0005_pascalcase_physical_columns").Migration
        create_models = {op.name: op for op in migration.operations if isinstance(op, migrations.CreateModel)}
        expected = {
            "UserAccountGroup": {"Id", "UserAccountId", "GroupId"},
            "UserAccountUserPermission": {"Id", "UserAccountId", "PermissionId"},
        }
        for name, columns in expected.items():
            self.assertIn(name, create_models)
            declared = {
                getattr(field, "db_column", None)
                for _, field in create_models[name].fields
            }
            self.assertTrue(columns.issubset(declared), f"{name}: missing {columns - declared}")
        sql_operations = [op for op in migration.operations if isinstance(op, migrations.RunSQL)]
        self.assertEqual(len(sql_operations), 1)
        forward = " ".join(sql_operations[0].sql)
        reverse = " ".join(sql_operations[0].reverse_sql)
        for old, new in (("id", "Id"), ("useraccount_id", "UserAccountId"), ("group_id", "GroupId"), ("permission_id", "PermissionId")):
            self.assertIn(old, forward)
            self.assertIn(new, forward)
            self.assertIn(old, reverse)
            self.assertIn(new, reverse)

    def test_many_to_many_state_changes_do_not_emit_schema_alter_field(self):
        from importlib import import_module

        migration = import_module("user.migrations.0005_pascalcase_physical_columns").Migration
        direct_m2m_alters = []
        state_only_m2m_alters = []
        for operation in migration.operations:
            if isinstance(operation, migrations.AlterField) and operation.field.many_to_many:
                direct_m2m_alters.append(operation)
            if isinstance(operation, migrations.SeparateDatabaseAndState):
                for state_operation in operation.state_operations:
                    if isinstance(state_operation, migrations.AlterField) and state_operation.field.many_to_many:
                        state_only_m2m_alters.append(state_operation)
        self.assertFalse(direct_m2m_alters, "M2M through changes must not invoke schema editor AlterField")
        self.assertEqual(len(state_only_m2m_alters), 2)
        self.assertTrue(all(not operation.database_operations for operation in migration.operations if isinstance(operation, migrations.SeparateDatabaseAndState)))
