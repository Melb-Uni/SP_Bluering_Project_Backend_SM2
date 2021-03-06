# Generated by Django 3.0.6 on 2021-05-06 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('git', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GitCommitCounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('space_key', models.CharField(max_length=256)),
                ('commit_counts', models.CharField(max_length=256)),
                ('query_date', models.IntegerField()),
            ],
            options={
                'db_table': 'git_commit_counts',
            },
        ),
        migrations.AlterField(
            model_name='studentcommitcounts',
            name='relation_id',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='studentcommitcounts',
            name='space_key',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
