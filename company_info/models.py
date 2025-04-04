from django.db import models

# company_info/models/base.py
from django.db import models
from django.db import models
import uuid
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator


class UUIDMixin(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Company(UUIDMixin, models.Model):
    # Scelte per campi con opzioni predefinite
    LEGAL_FORM_CHOICES = [
        ('SPA', 'Società per Azioni'),
        ('SRL', 'Società a Responsabilità Limitata'),
        ('SRLS', 'Società a Responsabilità Limitata Semplificata'),
        ('SNC', 'Società in Nome Collettivo'),
        ('SAS', 'Società in Accomandita Semplice'),
        ('DITTA_IND', 'Ditta Individuale'),
        ('COOP', 'Società Cooperativa'),
        ('ALTRO', 'Altro'),
    ]

    SEASONALITY_CHOICES = [
        ('NONE', 'Nessuna stagionalità'),
        ('SUMMER', 'Estiva'),
        ('WINTER', 'Invernale'),
        ('HOLIDAY', 'Periodi festivi'),
        ('CUSTOM', 'Personalizzata'),
    ]

    # Informazioni Generali sul Rischio
    vat_number = models.CharField(max_length=16, verbose_name="P.IVA", blank=False, null=False)
    legal_form = models.CharField(max_length=10, choices=LEGAL_FORM_CHOICES, verbose_name="Forma giuridica",
                                  blank=False, null=False)
    ateco_code = models.CharField(max_length=10, verbose_name="Codice Ateco", blank=False, null=False)

    # Informazioni sull'attività
    activity = models.CharField(max_length=100, verbose_name="Attività", blank=True)
    activity_description = models.TextField(verbose_name="Descrizione Attività", blank=True)
    annual_turnover = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Fatturato annuo", blank=True,
                                          null=True)
    employees = models.PositiveIntegerField(verbose_name="Numero di addetti", blank=True, null=True)
    seasonality = models.CharField(max_length=10, choices=SEASONALITY_CHOICES, verbose_name="Stagionalità", blank=True)

    # Indirizzo e contatti
    address = models.CharField(max_length=255, verbose_name="Indirizzo", blank=True)
    city = models.CharField(max_length=100, verbose_name="Città", blank=True)
    postal_code = models.CharField(max_length=10, verbose_name="Codice Postale", blank=True)
    region = models.CharField(max_length=100, verbose_name="Regione", blank=True)
    country = models.CharField(max_length=100, verbose_name="Paese", blank=True, default="Italia")

    # Informazioni di contatto
    email = models.EmailField(verbose_name="Email", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Telefono", blank=True)
    contact_person = models.CharField(max_length=100, verbose_name="Persona di contatto", blank=True)

    # Metadati
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data di creazione")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data di modifica")

    class Meta:
        verbose_name = "Azienda"
        verbose_name_plural = "Aziende"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vat_number} - {self.activity}"


class UnderwritingAssessment(UUIDMixin, models.Model):
    # Nuovo modello per i campi restanti, legati alla valutazione di underwriting

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='underwriting_assessments')
    underwriting_year = models.IntegerField()  # Anno di underwriting

    # Manteniamo i campi non spostati nella checklist
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    win_probability = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    customer_relation = models.CharField(max_length=100, blank=True, null=True)
    broker_relation = models.CharField(max_length=100, blank=True, null=True)
    similar_deals_won = models.IntegerField(blank=True, null=True)
    average_deal_size = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    conversion_time = models.DurationField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Underwriting Assessment'
        verbose_name_plural = 'Underwriting Assessments'
        # Garantire che ogni valutazione sia unica per compagnia e anno
        unique_together = ['company', 'underwriting_year']
        ordering = ['-underwriting_year']

    def __str__(self):
        return f"{self.company.vat_number} - Assessment {self.underwriting_year}"


class ChecklistKind(UUIDMixin, models.Model):
    """
    Rappresenta i diversi tipi di verifiche che possono essere eseguite nella checklist.
    Ogni tipo ha un nome univoco.
    """
    name = models.CharField(max_length=100, unique=True)
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Valore di valutazione da 0 a 10"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tipo di Checklist'
        verbose_name_plural = 'Tipi di Checklist'
        ordering = ['name']


class UnderwritingChecklist(UUIDMixin, models.Model):
    """
    Rappresenta le righe della checklist di sottoscrizione associate a una valutazione di underwriting.
    Utilizza ChecklistKind per definire i vari tipi di verifiche in modo dinamico.
    """
    # Collegamento all'assessment di underwriting
    assessment = models.ForeignKey('UnderwritingAssessment', on_delete=models.CASCADE,
                                   related_name='checklist_items')

    # Collegamento al tipo di checklist
    kind = models.ForeignKey('ChecklistKind', on_delete=models.CASCADE,
                             related_name='checklist_items')

    # Valore assegnato (da 0 a 10)
    value = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Valore da 0 a 10"
    )

    # Note specifiche per questa verifica
    notes = models.TextField(blank=True, null=True,
                             help_text="Note aggiuntive sulla verifica")

    # Indica se questa specifica verifica è conforme
    is_compliant = models.BooleanField(default=True,
                                       help_text="Indica se l'azienda è conforme per questo aspetto")

    completed_by = models.CharField(max_length=100, blank=True, null=True,
                                    help_text="Nome della persona che ha completato la verifica")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Checklist Item'
        verbose_name_plural = 'Checklist Items'
        ordering = ['-created_at']
        # Evita duplicazione dello stesso tipo di checklist per lo stesso assessment
        unique_together = ['assessment', 'kind']

    def __str__(self):
        return f"{self.kind.name}: {self.value}/10 - {self.assessment.company.vat_number}"
