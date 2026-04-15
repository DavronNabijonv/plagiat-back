from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

SKIP_APPS = {'admin', 'auth', 'contenttypes', 'sessions'}


class Command(BaseCommand):
    help = "Backup DB -> Prod DB migration (safe FK version)"

    def add_arguments(self, parser):
        parser.add_argument('--backup-db', default='backup')

    def handle(self, *args, **options):
        self.backup_db = options['backup_db']
        self.stdout.write("\n🚀 START MIGRATION\n")

        self.user_map = {}
        self.document_map = {}

        self.sync_users()
        self.migrate_models()

        self.stdout.write(self.style.SUCCESS("\n✅ DONE"))

    def sync_users(self):
        self.stdout.write("\n━━ USERS ━━")
        qs = User.objects.using(self.backup_db).all()
        for u in qs:
            phone = getattr(u, "phone", None)
            if not phone:
                continue
            old_id = u.pk
            try:
                prod = User.objects.using('default').get(phone=phone)
                self.user_map[old_id] = prod.id
            except User.DoesNotExist:
                u.pk = None
                u.save(using='default')
                self.user_map[old_id] = u.pk

    def migrate_models(self):
        models_order = [
            "shared.Document",
            "shared.DocumentResult",
            "shared.Order",
            "payme.PaymeTransactions",
        ]
        for model_path in models_order:
            app_label, model_name = model_path.split(".")
            model = apps.get_model(app_label, model_name)
            self.migrate_model(model)

    def migrate_model(self, model):
        qs = model.objects.using(self.backup_db).all()
        count = qs.count()
        self.stdout.write(f"\n🔷 {model.__name__} ({count})")

        with transaction.atomic(using='default'):
            for obj in qs:
                old_pk = obj.pk
                data = {}
                should_skip = False

                for field in model._meta.concrete_fields:
                    if field.primary_key:
                        continue

                    if field.is_relation and field.many_to_one:
                        rel = field.related_model.__name__
                        old_id = getattr(obj, field.attname)
                        if old_id is None:
                            data[f"{field.name}_id"] = None
                            continue
                        new_id = self.resolve_fk(rel, old_id)
                        if rel in ["User", "Document"]:
                            if new_id is None:
                                should_skip = True
                                break
                            data[f"{field.name}_id"] = new_id
                            continue
                        data[f"{field.name}_id"] = new_id
                        continue

                    data[field.name] = getattr(obj, field.attname)

                if should_skip:
                    self.stdout.write(f"⛔️ SKIP {model.__name__} id={old_pk}")
                    continue

                if model.__name__ == "Order":
                    data["type"] = data.get("type") or "document"

                instance, created = model.objects.using('default').update_or_create(
                    pk=old_pk,
                    defaults=data
                )


                if model.__name__ == "Document":
                    self.document_map[old_pk] = instance.pk


                action = "✅ CREATED" if created else "🔄 UPDATED"
                self.stdout.write(f"  {action} {model.__name__} id={old_pk}")

    def resolve_fk(self, model_name, old_id):
        if model_name == "User":
            return self.user_map.get(old_id)
        if model_name == "Document":
            return self.document_map.get(old_id)
        return None

    def topological_sort(self, models):
        visited = set()
        result = []

        def visit(m):
            if m in visited:
                return
            visited.add(m)
            for f in m._meta.get_fields():
                if hasattr(f, 'remote_field') and f.remote_field:
                    visit(f.remote_field.model)
            result.append(m)

        for m in models:
            visit(m)
        return result
