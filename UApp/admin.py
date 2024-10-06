from django.contrib import admin
from .models import Student, Equipment, Transaction, MedicalKit, Treatment


admin.site.site_header = 'DIMS Admin Dashboard'

# class TransactionAdmin(admin.ModelAdmin):
#     list_display = ('handled_by','student', 'equipment', 'Date','borrowed_time','returned_at', 'return_status')
#     list_filter = ['handled_by','status']
#     def Date(self, obj):
#         return obj.borrowed_at.date()  # This extracts only the date part
#     def borrowed_time(self, obj):
#         return obj.borrowed_at.time()
#     def return_status(self, obj):
#         return 'Returned' if obj.status else 'Not returned'


# Register your models here.
admin.site.register(Student)
admin.site.register(Equipment)
admin.site.register(MedicalKit)
admin.site.register(Treatment)
# admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Transaction)

