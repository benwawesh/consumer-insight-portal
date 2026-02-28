from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class CachedOffer(models.Model):
    """
    Cached offers from CPAGrip API with admin moderation controls
    """
    # Offer Details
    offer_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    payout = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    offer_link = models.URLField(max_length=500)
    offer_type = models.CharField(max_length=50)  # Email Submit, Zip Submit, etc.
    countries = models.CharField(max_length=200, help_text="Comma-separated country codes")
    
    # CPAGrip Dashboard Fields
    offer_image = models.URLField(max_length=500, blank=True, null=True, help_text="Thumbnail/offer image URL")
    net_epc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Net Earnings Per Click"
    )
    conversion_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Conversion rate percentage"
    )
    performance_percentage = models.IntegerField(
        default=0,
        help_text="Performance score/percentage"
    )
    offer_category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Main category (e.g., Mobile Install, Email/Zip Submit)"
    )
    required_device = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Required device (e.g., Android, iOS, Desktop)"
    )
    clicks = models.IntegerField(default=0, help_text="Number of clicks")
    leads = models.IntegerField(default=0, help_text="Number of leads/conversions")
    date_added = models.DateField(blank=True, null=True, help_text="Date offer was added")
    
    # Admin Control Fields
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Review Queue'),
            ('live', 'Live on Website'),
            ('rejected', 'Rejected'),
        ],
        default='pending',
        db_index=True
    )
    is_featured = models.BooleanField(default=False, help_text="Pin to top of listings")
    display_order = models.IntegerField(
        default=0,
        help_text="Manual ranking (lower number = higher priority)"
    )
    
    # Metadata
    last_fetched = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_offers'
    )
    
    class Meta:
        ordering = ['-is_featured', 'display_order', '-payout']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['payout']),
            models.Index(fields=['countries']),
            models.Index(fields=['offer_category']),
            models.Index(fields=['required_device']),
        ]
    
    def __str__(self):
        return f"{self.name} (${self.payout}) - {self.get_status_display()}"
    
    @property
    def is_live(self):
        return self.status == 'live'
    
    @property
    def net_cr(self):
        """Calculate Net Conversion Rate (leads/clicks)"""
        if self.clicks > 0:
            return Decimal(self.leads) / Decimal(self.clicks) * 100
        return Decimal('0.00')


class ConversionTracking(models.Model):
    """
    Track user conversions with detailed lead inspection data
    """
    tracking_id = models.CharField(max_length=100, unique=True, db_index=True)
    offer_id = models.CharField(max_length=50)
    offer_name = models.CharField(max_length=200)
    payout = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Lead Inspection Fields
    user_ip = models.GenericIPAddressField()
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('mobile', 'Mobile'),
            ('desktop', 'Desktop'),
            ('tablet', 'Tablet'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    user_agent = models.TextField()
    referrer = models.URLField(blank=True, null=True)
    
    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('flagged', 'Flagged for Review'),
        ],
        default='pending',
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Admin Notes
    admin_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user_ip']),
        ]
    
    def __str__(self):
        return f"{self.offer_name} - {self.status} - {self.user_ip}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def time_to_complete(self):
        """Calculate time from creation to completion"""
        if self.completed_at and self.created_at:
            return self.completed_at - self.created_at
        return None


class AdminSettings(models.Model):
    """
    Store admin-configurable settings
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    class Meta:
        verbose_name_plural = "Admin Settings"