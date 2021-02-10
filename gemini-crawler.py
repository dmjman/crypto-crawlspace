from datetime import datetime, timezone
from json     import load, loads
from requests import get, exceptions


CONFIGURATION_FILE_LOCATION: str = "./configuration.json"


def get_configuration() -> dict[str, str]:
    configuration: dict[str, str] = {}
    with open(CONFIGURATION_FILE_LOCATION, "r") as configuration_file:
        configuration = load(configuration_file)
    return configuration


def get_website_data(configuration: dict[str, str]) -> dict:
    api_url: str = configuration.get("api-url")
    api_header_key_title: str = configuration.get("api-header-key-title")
    api_key: str = configuration.get("api-key")

    if None in [api_url, api_header_key_title, api_key]:
        return {}
    
    headers: dict[str, str] = {
        "Accepts": "application/json",
        api_header_key_title: api_key
    }
    
    try:
        return loads(get(api_url, headers=headers).text)
    except (exceptions.ConnectionError, exceptions.Timeout, exceptions.TooManyRedirects):
        return {}


def get_crypto_data(configuration: dict[str, str]) -> dict[str, tuple[str, float]]:
    currency_filter: list[str] = configuration.get("currency-filter")
    return {symbol: (currency["name"], currency["quote"]["USD"]["price"]) \
        for currency in get_website_data(configuration)["data"] \
            if (symbol := currency["symbol"]) in currency_filter}


def create_display_list(crypto_map: dict[str, tuple[str, float]]) -> list[str]:
    max_price: str = f"{max([round(price, 4) for _, (_, price) in crypto_map.items()]):.4f}"
    return [f"{name}{(10-len(name))*' '}({symbol}){(4-len(symbol)+len('()')) * ' '}-  $ {(len(max_price)-len(f'{price:.4f}'))* ' '}{price:.4f}" \
        for symbol, (name, price) in crypto_map.items()] 


def create_gemini_page_from_formatted_data(formatted_data: list[str], configuration: dict[str, str]) -> tuple[int, str]:
    capsule_header: str = ""
    capsule_footer: str = ""

    header_loaction: str = configuration.get("capsule-header-location")
    footer_location: str = configuration.get("capsule-footer-location")
    if None in [header_loaction, footer_location]:
        return 1, ""
    
    with open(header_loaction, "r") as header:
        capsule_header = "".join(header.readlines())
    with open(footer_location, "r") as footer:
        capsule_footer = "".join(footer.readlines())

    return 0, (
        capsule_header + (
            "## Prices\n"
            f"Prices updated on {datetime.now(timezone.utc).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M UTC')}\n"
            "Prices update about every 5 minutes\n\n"
            "``` Cryptocurrency prices\n") +
        "\n".join(formatted_data) + "\n```\n" +
        capsule_footer
    )


def write_gemini_page(gemini_data: str, output_location: str) -> int:
    if not output_location:
        return 1

    with open(output_location, "w") as out:
        out.write(gemini_data)

    return 0


def main() -> int:
    configuration: dict = get_configuration()
    return write_gemini_page(
        create_gemini_page_from_formatted_data(create_display_list(get_crypto_data(configuration)), configuration)[1],
        configuration.get("output-location"))


if __name__ == "__main__":
    exit(main())
