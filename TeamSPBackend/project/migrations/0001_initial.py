# Generated by Django 3.0.6 on 2021-04-28 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectCoordinatorRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coordinator_id', models.IntegerField(max_length=256)),
                ('space_key', models.CharField(max_length=256)),
                ('git_url', models.CharField(max_length=256)),
                ('jira_project', models.CharField(max_length=256)),
            ],
            options={
                'db_table': 'project_coordinator_relation',
            },
        ),
    ]
