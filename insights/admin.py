from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin import SimpleListFilter
from .models import CachedOffer, ConversionTracking, AdminSettings
from .services import fetch_and_cache_offers


class CountryFilter(SimpleListFilter):
    title = 'Country'
    parameter_name = 'country'
    
    def lookups(self, request, model_admin):
        from .models import CachedOffer
        countries = set()
        for offer in CachedOffer.objects.all():
            if offer.countries:
                for country in offer.countries.split(','):
                    countries.add(country.strip())
        
        sorted_countries = sorted(list(countries))
        # Add "All" option at the top
        return [('', 'All')] + [(c, c) for c in sorted_countries]
    
    def queryset(self, request, queryset):
        # If no country selected or "All" selected, return all offers
        if not self.value():
            return queryset
        # If specific country selected, filter by it
        return queryset.filter(countries__contains=self.value())


class CategoryFilter(SimpleListFilter):
    title = 'Category'
    parameter_name = 'category'
    
    def lookups(self, request, model_admin):
        from .models import CachedOffer
        categories = set()
        for offer in CachedOffer.objects.all():
            if offer.offer_category:
                categories.add(offer.offer_category)
        
        sorted_categories = sorted(list(categories))
        return [('', 'All')] + [(c, c) for c in sorted_categories]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(offer_category=self.value())
        return queryset


class StatusFilter(SimpleListFilter):
    title = 'Status'
    parameter_name = 'status_filter'
    
    def lookups(self, request, model_admin):
        return [
            ('', 'All'),
            ('live', 'Live'),
            ('pending', 'Pending'),
            ('rejected', 'Rejected'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(CachedOffer)
class CachedOfferAdmin(admin.ModelAdmin):
    list_display = ['offer_thumbnail', 'name', 'payout', 'net_epc', 'net_cr', 'countries_display', 'offer_category', 'required_device_display', 'status', 'is_featured']
    list_filter = [StatusFilter, CountryFilter, CategoryFilter, 'is_featured', 'required_device']
    search_fields = ['name', 'offer_id', 'description', 'offer_category']
    list_editable = ['status', 'is_featured']
    ordering = ['-payout']
    list_per_page = 50
    
    fieldsets = (
        ('Offer Information', {'fields': ('name', 'description', 'payout', 'offer_link', 'offer_type', 'offer_category')}),
        ('Performance Metrics', {'fields': ('net_epc', 'conversion_rate', 'performance_percentage', 'clicks', 'leads')}),
        ('Geographic & Device', {'fields': ('countries', 'required_device', 'offer_image')}),
        ('Publication Control', {'fields': ('status', 'is_featured', 'display_order')}),
        ('Metadata', {'fields': ('offer_id', 'date_added', 'last_fetched', 'created_at', 'reviewed_at', 'reviewed_by'), 'classes': ('collapse',)}),
    )
    
    readonly_fields = ['offer_id', 'last_fetched', 'created_at', 'reviewed_at', 'reviewed_by', 'net_cr']
    actions = ['approve_offers', 'reject_offers', 'feature_offers', 'unfeature_offers']
    
    def offer_thumbnail(self, obj):
        if obj.offer_image:
            return format_html('<img src="{}" alt="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;">', obj.offer_image, obj.name)
        return mark_safe('<span style="color: #999;">No Image</span>')
    offer_thumbnail.short_description = 'Image'
    offer_thumbnail.allow_tags = True
    
    def net_cr(self, obj):
        cr = obj.net_cr
        if cr > 0:
            return format_html('<span style="color: #4caf50; font-weight: bold;">{:.2f}%</span>', cr)
        return '0.00%'
    net_cr.short_description = 'Net CR'
    
    def countries_display(self, obj):
        if not obj.countries:
            return 'All'
        codes = [c.strip() for c in obj.countries.split(',')]
        display = ' '.join(codes[:3])
        if len(codes) > 3:
            display += f' (+{len(codes)-3})'
        return display
    countries_display.short_description = 'Country'
    
    def required_device_display(self, obj):
        if not obj.required_device:
            return 'All'
        device = obj.required_device.lower()
        if 'android' in device:
            return '📱 Android'
        elif 'ios' in device:
            return '📱 iOS'
        elif 'desktop' in device:
            return '💻 Desktop'
        return obj.required_device
    required_device_display.short_description = 'Device'
    
    def approve_offers(self, request, queryset):
        count = queryset.update(status='live')
        self.message_user(request, f'{count} offer(s) approved successfully.')
    approve_offers.short_description = 'Approve selected offers'
    
    def reject_offers(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} offer(s) rejected.')
    reject_offers.short_description = 'Reject selected offers'
    
    def feature_offers(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} offer(s) featured.')
    feature_offers.short_description = 'Feature selected offers'
    
    def unfeature_offers(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f'{count} offer(s) unfeatured.')
    unfeature_offers.short_description = 'Unfeature selected offers'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [path('sync-cpargip/', self.admin_site.admin_view(self.sync_with_cpargip), name='insights_cachedoffer_sync')]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['sync_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def sync_with_cpargip(self, request):
        try:
            result = fetch_and_cache_offers(status='pending')
            if result is None:
                messages.error(request, 'Failed to connect to CPAGrip API. Please check your API credentials and try again.')
            elif result == 0:
                messages.warning(request, 'No new offers found. All offers may already be cached.')
            else:
                messages.success(request, f'Successfully imported {result} new offers for review.')
        except Exception as e:
            messages.error(request, f'Error syncing with CPAGrip: {str(e)}')
        return HttpResponseRedirect(reverse('admin:insights_cachedoffer_changelist'))


@admin.register(ConversionTracking)
class ConversionTrackingAdmin(admin.ModelAdmin):
    list_display = ['tracking_id', 'offer_name', 'payout', 'user_ip', 'device_type', 'status', 'created_at']
    list_filter = ['status', 'device_type', 'created_at']
    search_fields = ['tracking_id', 'offer_name', 'user_ip', 'user_agent']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['tracking_id', 'offer_id', 'offer_name', 'payout', 'user_ip', 'device_type', 'user_agent', 'referrer', 'created_at', 'completed_at', 'updated_at']
    actions = ['mark_completed', 'mark_failed', 'flag_for_review']
    
    def mark_completed(self, request, queryset):
        count = queryset.filter(status='pending').update(status='completed')
        self.message_user(request, f'{count} conversion(s) marked as completed.')
    mark_completed.short_description = 'Mark as completed'
    
    def mark_failed(self, request, queryset):
        count = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f'{count} conversion(s) marked as failed.')
    mark_failed.short_description = 'Mark as failed'
    
    def flag_for_review(self, request, queryset):
        count = queryset.filter(status='pending').update(status='flagged')
        self.message_user(request, f'{count} conversion(s) flagged for review.')
    flag_for_review.short_description = 'Flag for review'


@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_at']
    search_fields = ['key', 'description']
    ordering = ['key']


admin.site.site_header = 'Consumer Insight Portal Admin'
admin.site.site_title = 'Insights Admin'
admin.site.index_title = 'Welcome to Consumer Insight Portal Admin'
