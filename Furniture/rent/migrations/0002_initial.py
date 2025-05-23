# Generated by Django 5.1.7 on 2025-04-15 02:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('rent', '0001_initial'),
        ('user', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='rent',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rentals', to='user.product'),
        ),
        migrations.AddField(
            model_name='rent',
            name='renter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rentals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rentableproduct',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rentable_products', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rental',
            name='rentable_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rent.rentableproduct'),
        ),
        migrations.AddField(
            model_name='rental',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
