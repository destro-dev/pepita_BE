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

    def list(self, request):
        """
        Returns a list of all saved companies.
        """
        companies = self.get_queryset()
        serializer = self.get_serializer(companies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def fetch_contractors(self, request):
        """
        Recupera informazioni sui contractor da un servizio esterno e popola/aggiorna
        il modello Company.
        """
        # URL del servizio esterno
        external_service_url = "https://staging-ayako.riskapp.it/midori/v02/negotiation/contractors/"

        try:
            # Disable SSL verification warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Chiamata al servizio esterno
            headers = {
                'Authorization': 'JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQzNzk1MzA2LCJqdGkiOiJmNTk1MmU1MGY2MjY0MjNmODMzNzMwMjg3OTVmYWYyOCIsInVzZXJuYW1lIjoidXNlci5hZG1pbiIsImlkIjo0MjgsInV1aWQiOiIxM2E0NmZiMC03NzdkLTQxNjUtYTc0MC1kNzA4NDc3ZDE4NzEiLCJlbWFpbCI6InRlc3RAdGVzdC50ZXN0IiwiZmlyc3RfbmFtZSI6IlVzZXIiLCJsYXN0X25hbWUiOiJBZG1pbiIsImxhbmd1YWdlIjoiaXQiLCJvcmdhbml6YXRpb24iOiJJbnRlc2EgU2FuUGFvbG8gQXNzaWN1cmEiLCJzbGFfbGV2ZWwiOiIwNTAwIiwic2xhX2V4cGlyZSI6IjIwMjctMTItMTYiLCJzdXJ2ZXlzIjp0cnVlLCJyaXNrZ3JhZGl…lYXRoZXJfZGF0YSI6ZmFsc2UsImNvbmRvbWluaXVtcyI6ZmFsc2UsImNvbXBhbmllcyI6dHJ1ZSwicHJpdmF0ZXMiOmZhbHNlLCJuZWdvdGlhdGlvbnMiOnRydWUsIm1hc3NpdmVfaW5zZXJ0aW9uIjp0cnVlLCJjb250cmFjdHNfYW5hbHl6ZXIiOmZhbHNlLCJpc19zc28iOmZhbHNlLCJuYXRjYXRfcmF0ZXMiOnRydWUsIm1hbmFnZXIiOnRydWUsImF2YXRhciI6Ii9tZWRpYS91c2VycHJvZmlsZS9hdmF0YXIvMTNhNDZmYjAtNzc3ZC00MTY1LWE3NDAtZDcwODQ3N2QxODcxL2RlZmF1bHQtYXZhdGFyLnBuZyIsImxvZ28iOiIiLCJqd3RzZXNzaWQiOiJmODhjMDU0Ny02MTFkLTQyZjAtODc4Ni1jODBlMzBhNmIzMDkifQ.Oo7NbfHLHtpp8DxXJPnccVx8TUPxsFPji479OmOasWE'
            }
            
            response = requests.get(
                external_service_url,
                headers=headers,
                verify=False,  # Disable SSL verification for development
                timeout=30  # Add timeout
            )

            # Check if the response is successful
            if response.status_code != 200:
                return Response(
                    {"error": f"API returned status code {response.status_code}: {response.text}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            try:
                contractors_data = response.json()
            except ValueError as e:
                return Response(
                    {"error": f"Invalid JSON response: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if not isinstance(contractors_data, list):
                return Response(
                    {"error": "Expected a list of contractors in the response"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            created_companies = []
            for contractor in contractors_data:
                try:
                    # Mappatura dei dati ricevuti al modello Company
                    company_info = {
                        'vat_number': contractor.get('vat_number'),
                        'legal_form': 'ALTRO',  # Default value since it's not provided in the API
                        'ateco_code': contractor.get('activity'),  # Using activity as ateco_code
                        'activity': contractor.get('activity_full_description'),
                        'activity_description': contractor.get('activity_full_description'),
                        'annual_turnover': contractor.get('yearly_revenues'),
                        'address': contractor.get('address'),
                        'city': contractor.get('city'),
                        'postal_code': contractor.get('postcode'),
                        'region': contractor.get('province'),  # Using province as region
                        'country': contractor.get('country'),
                    }

                    # Crea o aggiorna l'azienda nel database
                    company, created = Company.objects.update_or_create(
                        vat_number=contractor.get('vat_number'),
                        defaults=company_info
                    )
                    created_companies.append(company)
                except Exception as e:
                    print(f"Error processing contractor {contractor.get('vat_number')}: {str(e)}")
                    continue

            # Prepara la risposta
            result = CompanySerializer(created_companies, many=True).data
            return Response(result, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            # Gestione degli errori di connessione o risposta
            print(f"Request error: {str(e)}")
            return Response(
                {"error": f"Errore nella comunicazione con il servizio esterno: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            # Gestione di altri errori
            print(f"Unexpected error: {str(e)}")
            return Response(
                {"error": f"Errore durante l'elaborazione: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
