# Generated by Django 4.2 on 2024-09-07 10:28

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('total_sales', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_transactions', models.IntegerField()),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
