# coding:utf-8
"""
Django administration setup
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: BSD
"""

from django.contrib import admin
from datetime import datetime

from pydici.leads.models import Lead, Client, ClientOrganisation, ClientCompany, ClientContact, Consultant, SalesMan, Mission, Staffing, Holiday

from pydici.leads.utils import send_lead_mail, capitalize


class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "short_description", "responsible", "salesman", "state", "due_date", "update_date_strf")
    fieldsets = [
        (None,              {"fields": ["name", "client", "description", "salesId"]}),
        ("État et suivi",   {"fields": ["responsible", "salesman", "state", "due_date", "start_date"]}),
        ("Staffing",        {"fields": ["staffing", "external_staffing", "sales"]}),
        (None,              {"fields": ["send_email",]})
        ]
    ordering = ("creation_date",)
    filter_horizontal=["staffing"]
    list_filter = ["state",]
    date_hierarchy = "update_date"
    search_fields = ["name", "description", "salesId",
                     "responsible__name",  "responsible__trigramme",
                     "salesman__name", "salesman__trigramme",
                     "client__contact__name", "client__organisation__company__name",
                     "client__organisation__name",
                     "staffing__trigramme", "staffing__name"]

    def save_model(self, request, obj, form, change):
        mail=False
        if obj.send_email:
            mail=True
            obj.send_email=False
        obj.save()
        form.save_m2m() # Save many to many relations
        if mail:
            try:
                send_lead_mail(obj, fromAddr="%s@newarch.Fr" % request.user.username,
                               fromName="%s %s" % (request.user.first_name, request.user.last_name))
                request.user.message_set.create(message="Ce lead a été envoyé par mail au plan de charge.")
            except Exception, e:
                request.user.message_set.create(message="Échec d'envoi du mail : %s" % e)

        # Create or update mission object if needed
        mission, mission_does_not_exist=Mission.objects.get_or_create(lead=obj)
        if obj.state in ("OFFER_SENT", "NEGOCIATION", "WIN") and mission_does_not_exist:
            currentMonth=datetime.now()
            mission.lead=obj
            mission.save()
            # Create default staffing
            for consultant in obj.staffing.all():
                staffing=Staffing()
                staffing.mission=mission
                staffing.consultant=consultant
                staffing.staffing_date=currentMonth
                staffing.update_date=currentMonth
                staffing.last_user="-"
                staffing.save()
            request.user.message_set.create(message="Une mission a été initialisée dans le plan de charge pour cette affaire.")
        if obj.state=="WIN":
            mission.probability=100
            mission.active=True
            mission.save()
            request.user.message_set.create(message="La probabilité de la mission a été mise à 100 % dans le plan de charge")
        elif obj.state in ("LOST", "FORGIVEN", "SLEEPING"):
            mission.probability=0
            mission.active=False
            mission.save()
            request.user.message_set.create(message="La mission correspondante a été archivée dans le plan de charge")



class ClientContactAdmin(admin.ModelAdmin):
    list_display=("name", "function", "email", "phone")
    odering=("name")
    search_fields=["name", "function"]

class SalesManAdmin(admin.ModelAdmin):
    list_display=("name", "company", "trigramme", "email", "phone")
    odering=("name")
    search_fields=["name", "trigramme"]

class ClientOrganisationAdmin(admin.ModelAdmin):
    fieldsets=[(None,    {"fields": ["company", "name"] } ),]
    list_display=("company", "name",)
    list_display_links=("company", "name",)
    ordering=("name",)
    search_fields=("name",)

class ClientOrganisationAdminInline(admin.TabularInline):
    model=ClientOrganisation

class ClientCompanyAdmin(admin.ModelAdmin):
    list_display=("name",)
    ordering=("name",)
    search_fields=("name",)

class ClientAdmin(admin.ModelAdmin):
    list_display=("organisation", "salesOwner", "contact")
    ordering=("organisation",)
    search_fields=("organisation__company__name", "organisation__name", "contact__name")

class ConsultantAdmin(admin.ModelAdmin):
    list_display=("name", "trigramme", "productive")
    search_fields=("name", "trigramme")
    ordering=("name",)

class MissionAdmin(admin.ModelAdmin):
    list_display=("lead", "description", "nature", "probability", "active", "update_date")
    search_fields=("lead__name", "description", "lead__client__organisation__company__name",
                   "lead__client__contact__name")
    ordering=("lead", "description")
    date_hierarchy="update_date"
    list_filter=["nature", "probability", "active"]

class HolidayAdmin(admin.ModelAdmin):
    list_display=("day", "description")
    date_hierarchy="day"

admin.site.register(Lead, LeadAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(ClientOrganisation, ClientOrganisationAdmin)
admin.site.register(ClientCompany, ClientCompanyAdmin)
admin.site.register(ClientContact, ClientContactAdmin)
admin.site.register(Consultant, ConsultantAdmin)
admin.site.register(SalesMan, SalesManAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Holiday, HolidayAdmin)