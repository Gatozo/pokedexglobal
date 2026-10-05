from .test_auth import AuthenticationBackendTests, AuthenticationFormsTests, ViewsAndFlowTests
from .test_views import PokedexTrackerTests, FrontendInteractivityInvariantsTests, NationalGenerationBarTests
from .test_catalogs import (
    CompiledCatalogsAndServiceTests,
    PokemonRubyGen3Tests,
    PokemonSapphireGen3Tests,
    PokemonEmeraldGen3Tests,
    PokemonFireRedGen3Tests,
)
from .test_fixtures import FixtureExportTests, Gen2MechanicsAndExclusivesTests

__all__ = [
    'AuthenticationBackendTests',
    'AuthenticationFormsTests',
    'ViewsAndFlowTests',
    'PokedexTrackerTests',
    'FrontendInteractivityInvariantsTests',
    'NationalGenerationBarTests',
    'CompiledCatalogsAndServiceTests',
    'PokemonRubyGen3Tests',
    'PokemonSapphireGen3Tests',
    'PokemonEmeraldGen3Tests',
    'PokemonFireRedGen3Tests',
    'FixtureExportTests',
    'Gen2MechanicsAndExclusivesTests',
]
