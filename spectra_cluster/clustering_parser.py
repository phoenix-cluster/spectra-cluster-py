# ------------------------------
# This is a first implementation of
# a parser class to process
# .clustering output files
# -------------------------------


from . import objects


class ClusteringParser:
    """Parses .clustering output files created by the spectra-cluster applications.
    """

    def __init__(self, clustering_file):
        """
        Processes the passed .clustering file
        :param clustering_file: Path to the file to process
        :return:
        """
        self.clustering_file = clustering_file

    def __iter__(self):
        return self._get_iterator()

    def _get_iterator(self):
        """
        Iterates over all clusters in a file
        :return: The next Cluster
        """
        spectra = list()
        cur_id = None
        precursor_mz = None
        consensus_mz = list()
        consensus_intens = list()

        with open(self.clustering_file, "r") as clustering_input:
            for line in clustering_input:
                if line.strip() == "=Cluster=":
                    # create and return the cluster
                    if cur_id is not None:
                        cluster = objects.Cluster(cur_id, precursor_mz, consensus_mz, consensus_intens, spectra)
                        yield cluster

                    # reset parameters
                    cur_id = None
                    precursor_mz = None
                    consensus_mz = list()
                    consensus_intens = list()
                    spectra = list()

                    continue

                # process the spectrum
                if line.lstrip()[0:4] == "SPEC":
                    spectra.append(ClusteringParser._parse_spec_line(line))
                    continue

                # process standard fields
                if line.lstrip()[0:3] == "id=":
                    cur_id = line[3:].rstrip()
                if line.lstrip()[0:16] == "av_precursor_mz=":
                    precursor_mz = float(line[16:].rstrip())
                if line.lstrip()[0:13] == "consensus_mz=":
                    consensus_mz = [float(s) for s in line[13:].rstrip().split(",")]
                if line.lstrip()[0:17] == "consensus_intens=":
                    consensus_intens = [float(s) for s in line[17:].rstrip().split(",")]

        # process the last cluster
        if cur_id is not None:
            yield cluster

    @staticmethod
    def _parse_spec_line(line):
        """
        Parses a .clustering SPEC line and creates the corresponding PSM object
        :param line: A String representing the SPEC line.
        :return: A PSM object.
        """
        fields = line.split("\t")

        if len(fields) != 9:
            raise Exception("Invalid SPEC line encountered: " + line)

        title = fields[1]
        sequences = fields[3].split(",")
        prec_mz = float(fields[4])
        # charge is stored as float just in case
        charge = float(fields[5])
        taxids = fields[6].split(",")
        ptms = ClusteringParser._parse_ptms(fields[7])

        return objects.PSM(title, sequences, prec_mz, charge, taxids, ptms)

    @staticmethod
    def _parse_ptms(ptm_string):
        """
        Creates a list of PTMs based on a PTM specification string.
        :param ptm_string: String defining the PTMs in a .clustering SPEC line.
        :return: List of PTMs
        """
        if len(ptm_string) < 1:
            return list()

        ptm_strings = ptm_string.split(",")
        ptms = list()

        for cur_ptm_string in ptm_strings:
            fields = cur_ptm_string.split("-")
            if len(fields) != 2:
                raise Exception("Invalid PTM definition encountered: " + cur_ptm_string)

            ptms.append(objects.PTM(int(fields[0]), fields[1]))

        return ptms
