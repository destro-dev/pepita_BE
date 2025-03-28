from django.shortcuts import render

from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
import requests

from .models import Company
from .serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire le operazioni CRUD su Company, con funzionalità
    aggiuntiva di popolamento da servizio esterno.
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=False, methods=['post'])
    def fetch_from_external(self, request):
        """
        Recupera informazioni aziendali da un servizio esterno e popola/aggiorna
        il modello Company.

        Parametri richiesti nel request.data:
        - vat_number: Partita IVA dell'azienda da cercare
        """
        vat_number = request.data.get('vat_number')
        if not vat_number:
            return Response(
                {"error": "È necessario fornire una partita IVA"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # URL del servizio esterno (da configurare nelle impostazioni)
        external_service_url = "https://api.esempio-servizio.it/company-info"

        try:
            # Chiamata al servizio esterno
            response = requests.get(
                external_service_url,
                params={'vat_number': vat_number},
                # Aggiungi eventuali headers necessari per l'autenticazione
                # headers={'Authorization': 'Bearer your_token'}
            )

            # Verifica della risposta
            response.raise_for_status()  # Solleva un'eccezione per risposte HTTP di errore
            company_data = response.json()

            # Mappatura dei dati ricevuti al modello Company
            company_info = {
                'vat_number': company_data.get('vat_number'),
                'legal_form': company_data.get('legal_form'),
                'ateco_code': company_data.get('ateco_code'),
                'activity': company_data.get('activity'),
                'activity_description': company_data.get('activity_description'),
                'annual_turnover': company_data.get('annual_turnover'),
                'employees': company_data.get('employees'),
                'seasonality': company_data.get('seasonality'),
                'address': company_data.get('address'),
                'city': company_data.get('city'),
                'postal_code': company_data.get('postal_code'),
                'region': company_data.get('region'),
                'country': company_data.get('country'),
                'email': company_data.get('email'),
                'phone': company_data.get('phone'),
                'contact_person': company_data.get('contact_person'),
            }

            # Crea o aggiorna l'azienda nel database
            company, created = Company.objects.update_or_create(
                vat_number=vat_number,
                defaults=company_info
            )

            # Prepara la risposta
            result = CompanySerializer(company).data
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

            return Response(result, status=status_code)

        except requests.exceptions.RequestException as e:
            # Gestione degli errori di connessione o risposta
            return Response(
                {"error": f"Errore nella comunicazione con il servizio esterno: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            # Gestione di altri errori
            return Response(
                {"error": f"Errore durante l'elaborazione: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
