from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0018_seed_web_applications_email_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="Provider",
            field=models.CharField(blank=True, db_column="Provider", max_length=60),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="ProviderRequestId",
            field=models.CharField(
                blank=True,
                db_column="ProviderRequestId",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="ProviderMessageId",
            field=models.CharField(
                blank=True,
                db_column="ProviderMessageId",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="ProviderResponseCode",
            field=models.CharField(
                blank=True,
                db_column="ProviderResponseCode",
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="ProviderResponsePayload",
            field=models.JSONField(
                blank=True,
                db_column="ProviderResponsePayload",
                default=dict,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="FailureReason",
            field=models.TextField(blank=True, db_column="FailureReason"),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="LastErrorCode",
            field=models.CharField(
                blank=True,
                db_column="LastErrorCode",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="RetryCount",
            field=models.PositiveIntegerField(default=0, db_column="RetryCount"),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="NextRetryAt",
            field=models.DateTimeField(
                blank=True,
                db_column="NextRetryAt",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="DeliveredAt",
            field=models.DateTimeField(
                blank=True,
                db_column="DeliveredAt",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="CorrelationId",
            field=models.CharField(
                blank=True,
                db_column="CorrelationId",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="emaildeliverylogs",
            name="RequestId",
            field=models.CharField(blank=True, db_column="RequestId", max_length=100),
        ),
        migrations.AlterField(
            model_name="emaildeliverylogs",
            name="Status",
            field=models.CharField(
                db_column="Status",
                default="PENDING",
                max_length=40,
            ),
        ),
    ]
