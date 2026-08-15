"""Where the venue data lives, and from which block.

The Wildcat endpoints are the public Goldsky ones the Wildcat app itself uses,
taken from `src/lib/protocol-stats/subgraph.ts` in `wildcat-app-v2`. No key.

Start blocks come from `networks.json` in `wildcat-finance/subgraph` and are
the arch controller deployments. They are the honest lower bound for a coverage
statement: before that block there was no protocol to have a history in.
"""

WILDCAT_DEPLOYMENTS = {
    "mainnet": {
        "endpoint": (
            "https://api.goldsky.com/api/public/"
            "project_cmheai1ym00jyx7p27qn46qtm/subgraphs/mainnet/v2.0.26/gn"
        ),
        "chain": "ethereum",
        "arch_controller": "0xfEB516d9D946dD487A9346F6fee11f40C6945eE4",
        "start_block": 18686645,
    },
    "plasma-mainnet": {
        "endpoint": (
            "https://api.goldsky.com/api/public/"
            "project_cmheai1ym00jyx7p27qn46qtm/subgraphs/plasma-mainnet/v2.0.22/gn"
        ),
        "chain": "plasma",
        "arch_controller": "0xdb2e0DE97d6d96aa56754635704a4273E0F348ae",
        "start_block": 1989721,
    },
}

DEFAULT_WILDCAT_NETWORK = "mainnet"

MORPHO_BLUE_ENDPOINT = "https://blue-api.morpho.org/graphql"

# The earliest market creation block across all 1,727 mainnet Morpho Blue
# markets, taken by paging the API rather than by trusting a launch
# announcement. It is the honest lower bound for a coverage statement: before
# it there was no market on this venue to have a history in.
MORPHO_BLUE_FIRST_MARKET_BLOCK = 18919623

# A separate product on a separate API: fixed-rate, fixed-maturity lending,
# REST rather than GraphQL, and on Base rather than mainnet. Keyless, and
# `/users/<address>/positions` and `/users/<address>/transactions` both answer.
# No adapter yet; the registry names it so a dossier does not imply otherwise.
MORPHO_MIDNIGHT_ENDPOINT = "https://api.morpho.org/v0/midnight"
