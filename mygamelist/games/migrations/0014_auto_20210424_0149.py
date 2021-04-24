# Generated by Django 3.2 on 2021-04-24 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0013_game_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='game',
            name='genres',
            field=models.ManyToManyField(to='games.Genre'),
        ),
    ]
