from abc import ABC, abstractmethod


class BaseAnalysisService(ABC):
    """
    Base class for all analysis services.

    Every scientific module should inherit
    from this class.
    """

    def execute(self):
        """
        Standard execution workflow.
        """

        self.validate()

        output = self.run()

        parsed = self.parse(output)

        result = self.import_results(parsed)

        return result

    @abstractmethod
    def validate(self):
        """
        Validate inputs.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Execute the analysis tool.
        """
        pass

    @abstractmethod
    def parse(self, output):
        """
        Parse tool output.
        """
        pass

    @abstractmethod
    def import_results(self, parsed):
        """
        Store results.
        """
        pass
    