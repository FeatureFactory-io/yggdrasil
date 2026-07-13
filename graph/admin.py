from django.contrib import admin

from graph.models import ChangeSet, Diagram, Element, Package, Relationship, Stereotype

admin.site.register(Stereotype)
admin.site.register(Package)
admin.site.register(Element)
admin.site.register(Relationship)
admin.site.register(Diagram)
admin.site.register(ChangeSet)
