# Generated by Django 5.0.3 on 2024-12-14 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_specialization_alter_user_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]