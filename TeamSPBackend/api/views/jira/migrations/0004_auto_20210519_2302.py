# Generated by Django 3.0.6 on 2021-05-19 13:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jira', '0003_auto_20210509_1650'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='individualcontributions',
            table='individual_contributions',
        ),
        migrations.AlterModelTable(
            name='jiracountbytime',
            table='jira_count_by_time',
        ),
    ]
