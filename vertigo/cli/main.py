import click
from os import getcwd
from pathlib import Path
from vertigo.mutation import MutationResult
from vertigo.mutation.truffle.truffle_campaign import TruffleCampaign
from vertigo.mutation.filters.sample_filter import SampleFilter
from vertigo.mutation.filters.exclude_filter import ExcludeFilter
from vertigo.test_runner.truffle import TruffleRunnerFactory
from vertigo.test_runner.exceptions import TestRunException
from vertigo.interfaces.truffle import Truffle

from tqdm import tqdm


@click.group(help="Mutation testing framework for smart contracts")
@click.version_option(1)
def cli():
    pass


@cli.command(help="Performs a mutation test campaign")
@click.option('--output', help="Output mutation test results to file", nargs=1, type=str)
@click.option('--network', help="Network names that vertigo can use", multiple=True)
@click.option('--truffle-location', help="Location of truffle cli", nargs=1, type=str, default="truffle")
@click.option('--sample-ratio', help="If this option is set. Vertigo will apply the sample filter with the given ratio", nargs=1, type=float)
@click.option('--exclude', help="Vertigo won't mutate files in these directories", multiple=True)
def run(output, network, truffle_location, sample_ratio, exclude):
    """ Run command """
    click.echo("[*] Starting mutation testing")

    # Setup global parameters
    truffle = Truffle(truffle_location)

    working_directory = getcwd()
    project_type = _directory_type(working_directory)
    filters = []
    if exclude:
        filters.append(ExcludeFilter(exclude))

    if project_type == "truffle":
        click.echo("[*] Starting analysis on truffle project")
        project_path = Path(working_directory)

        if not (project_path / "contracts").exists():
            click.echo("[-] No contracts directory in truffle project")
            return
        elif not (project_path / "test").exists():
            click.echo("[-] No test directory found in truffle project")
            return

        if sample_ratio:
            filters.append(SampleFilter(sample_ratio))

        try:
            campaign = TruffleCampaign(
                project_directory=project_path,
                truffle_compiler=truffle,
                truffle_runner_factory=TruffleRunnerFactory(truffle),
                networks=network,
                filters=filters
            )
        except:
            click.echo("[-] Encountered an error while setting up the mutation campaign")
            raise
    else:
        click.echo("[*] Could not find supported project directory in {}".format(working_directory))
        return

    click.echo("[*] Initializing campaign run ")

    try:
        campaign.setup()
        click.echo("[*] Checking validity of project")
        if not campaign.valid():
            click.echo("[-] We couldn't get valid results by running the truffle tests.\n Aborting")
            return
        click.echo("[+] The project is valid")
        click.echo("[*] Running analysis on {} mutants".format(len(campaign.mutations)))
        with tqdm(total=len(campaign.mutations), unit="mutant") as pbar:
            report = campaign.run(lambda: pbar.update(1) and pbar.refresh(), threads=max(len(network), 1))
        pbar.close()

    except TestRunException as e:
        click.echo("[-] Encountered an error while running the framework's test command:")
        click.echo(e)
        return
    except Exception as e:
        click.echo("[-] Encountered an error while running the mutation campaign")
        click.echo(e)
        raise

    click.echo("[*] Done with campaign run")
    click.echo("[+] Report:")
    click.echo(report.render())

    click.echo("[+] Survivors")
    for mutation in report.mutations:
        if mutation.result == MutationResult.LIVED:
            click.echo(str(mutation))

    if output:
        output_path = Path(output)
        if not output_path.exists() or click.confirm("[*] There already exists something at {}. Overwrite ".format(str(output_path))):
            click.echo("Result of mutation run can be found at: {}".format(output))
            output_path.write_text(report.render(with_mutations=True), "utf-8")
    click.echo("[*] Done! ")


def _directory_type(working_directory: str):
    """ Determines the current framework in the current directory """
    # jk, we only deal with truffle for now ^^'
    return "truffle"
