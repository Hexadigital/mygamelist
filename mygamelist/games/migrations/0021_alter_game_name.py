# Generated by Django 3.2 on 2021-04-30 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0020_merge_0018_auto_20210427_2205_0019_auto_20210430_0002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='name',
            field=models.CharField(max_length=150),
        ),
    ]
