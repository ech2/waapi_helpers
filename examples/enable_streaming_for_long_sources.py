from waapi import WaapiClient

from waapi_helpers import *

with WaapiClient() as client:
    for guid, max_dur_src in walk_wproj(client, '\\Actor-Mixer Hierarchy',
                                        ['id', 'maxDurationSource'], 'Sound'):
        if max_dur_src is None:
            continue
        if max_dur_src['trimmedDuration'] > 15:
            set_property_value(client, guid, 'IsStreamingEnabled', True)
