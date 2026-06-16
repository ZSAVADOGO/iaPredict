from django import forms
from .models import DbSource

class DataSourceForm(forms.ModelForm):
    class Meta:
        #Ancien code :
        """ model = DbSource
        fields = '__all__'
        widgets = {
            'password': forms.PasswordInput(render_value=True)
        } """
    
        model = DbSource
        # 1. OPTIMISATION : On exclut status et is_active pour ne pas surcharger le modal
        fields = ['name', 'db_type', 'host', 'port', 'database_name', 'username', 'password']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['password'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Si le mot de passe est laissé vide lors d'une modification, on garde l'ancien
        if not self.cleaned_data.get('password') and self.instance.pk:
            instance.password = DbSource.objects.get(pk=self.instance.pk).password
        else:
            instance.password = self.cleaned_data.get('password')
        if commit:
            instance.save()
        return instance
