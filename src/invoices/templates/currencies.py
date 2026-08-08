from __future__ import annotations

# Currency codes intentionally use the uppercase display form requested by the
# desktop UI. Stripe's REST API receives the same value lowercased at the
# provider adapter boundary. The list is the current documented Stripe
# presentment-currency set used as the common safe catalogue for the packaged
# Stripe/Refrens providers; Refrens accepts ISO 4217 currency codes.
SUPPORTED_INVOICE_CURRENCIES: tuple[str, ...] = (
    "USD", "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BIF", "BMD", "BND", "BOB", "BRL", "BSD", "BWP",
    "BYN", "BZD", "CAD", "CDF", "CHF", "CLP", "CNY", "COP", "CRC", "CVE", "CZK",
    "DJF", "DKK", "DOP", "DZD", "EGP", "ETB", "EUR", "FJD", "FKP", "GBP", "GEL",
    "GIP", "GMD", "GNF", "GTQ", "GYD", "HKD", "HNL", "HTG", "HUF", "IDR", "ILS",
    "INR", "ISK", "JMD", "JPY", "KES", "KGS", "KHR", "KMF", "KRW", "KYD", "KZT",
    "LAK", "LBP", "LKR", "LRD", "LSL", "MAD", "MDL", "MGA", "MKD", "MMK", "MNT",
    "MOP", "MUR", "MVR", "MWK", "MXN", "MYR", "MZN", "NAD", "NGN", "NIO", "NOK",
    "NPR", "NZD", "PAB", "PEN", "PGK", "PHP", "PKR", "PLN", "PYG", "QAR", "RON",
    "RSD", "RUB", "RWF", "SAR", "SBD", "SCR", "SEK", "SGD", "SHP", "SLE", "SOS",
    "SRD", "STD", "SZL", "THB", "TJS", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH",
    "UGX", "UYU", "UZS", "VND", "VUV", "WST", "XAF", "XCD", "XCG", "XOF", "XPF",
    "YER", "ZAR", "ZMW",
)

SUPPORTED_INVOICE_CURRENCY_SET = frozenset(SUPPORTED_INVOICE_CURRENCIES)

# Stripe's general zero-decimal charge currencies. ISK and UGX are handled by
# Stripe as special backward-compatible two-decimal API values and therefore
# are deliberately not included here.
STRIPE_ZERO_DECIMAL_CURRENCIES = frozenset(
    {"BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "MGA", "PYG", "RWF", "VND", "VUV", "XAF", "XOF", "XPF"}
)


def normalize_invoice_currency(value: str) -> str:
    code = str(value).strip().upper()
    if code not in SUPPORTED_INVOICE_CURRENCY_SET:
        raise ValueError("Choose a supported three-letter invoice currency.")
    return code
