# Generated by Django 4.2 on 2023-06-11 13:22

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Todo_List_App', '0019_task_createddate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='createdDate',
            field=models.DateTimeField(default=datetime.datetime(2023, 6, 11, 13, 22, 39, 206782, tzinfo=datetime.timezone.utc)),
        ),
    ]