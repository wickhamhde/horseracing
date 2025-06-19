import pandas as pd

def splitwt(wt, ind):
    try:
        wt = pd.to_numeric(wt.split("-")[0])
        return wt
    except:
        return pd.NA
    
def convert_distance_to_furlongs(df, col="Distance"):
    """
    Converts a distance string like '2m', '1m6f', '2m1½f' into a float number of furlongs.
    1 mile = 8 furlongs, so '1m6f' = 14 furlongs.
    """
    import re

    def parse_distance(value):
        if pd.isna(value):
            return np.nan

        # Extract miles and furlongs (including fractional furlongs)
        miles = 0
        furlongs = 0.0

        # Match miles and furlongs
        mile_match = re.search(r"(\d+)m", value)
        if mile_match:
            miles = int(mile_match.group(1))

        # Match furlongs including fractions (e.g., ½)
        furlong_match = re.search(r"(\d+)?(?:½)?f", value)
        if furlong_match:
            f_str = furlong_match.group(1)
            if f_str:
                furlongs += int(f_str)
            if "½f" in value:
                furlongs += 0.5

        return miles * 8 + furlongs

    df["distance_furlongs"] = df[col].apply(parse_distance)
    return df

def preprocess(df):
    df["Time"] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time
    df = df.rename(columns={"Date of Race":"date"})
    df["rid"] = df["date"].astype(str).str.replace("-","") + df["Track"] + df["Time"].apply(lambda x: f"{x.hour:02d}{x.minute:02d}")

    cols = ['rid'] + [col for col in df.columns if col != 'rid']
    df = df[cols]

    df["Place"] = pd.to_numeric(df["Place"], errors="coerce")
    df["Place"] = df["Place"].fillna(df["Runners"])

    df["normalized_position"] = (df["Place"].astype(int)) / (df["Runners"].astype(int))
    df.loc[df["normalized_position"] > 1, "normalized_position"] = 1
    
    df["Weight"]  = df["Weight"].str.replace("\xa0", "")

    df["weightSt"] = df["Weight"].apply(splitwt, ind=0)
    df["weightLb"] = df["Weight"].apply(splitwt, ind=1)
    df["weight_total_lb"] = df["weightSt"] * 14 + df["weightLb"]

    df["race_avg_weight"] = df.groupby("rid")["weight_total_lb"].transform("mean")
    df["weight_diff_pct_from_race_avg"] = (df["weight_total_lb"] - df["race_avg_weight"])/df["race_avg_weight"]

    df = convert_distance_to_furlongs(df)

    df['distance_bin'] = pd.qcut(df['distance_furlongs'], q=5)

    going_bin_map = {
        'FST': 'fast',
        'FRM': 'fast',
        'HRD': 'fast',
        'STFA': 'fast',
        'STFI': 'fast',

        'GD': 'good',
        'GTF': 'good',
        'GTS': 'good',
        'STG': 'good',
        'GTY': 'good',
        'YTG': 'good',
        'YTF': 'good',

        'SFT': 'soft',
        'STY': 'soft',
        'YLD': 'soft',
        'YTS': 'soft',

        'HVY': 'heavy',
        'HTS': 'heavy',
        'YSH': 'heavy',

        'SLW': 'slow',
        'STSL': 'slow',
        'STSF': 'slow',
        'STHE': 'slow',

        'STD': 'standard'
    }

    race_type_bin_map = {
        'Maiden': 'maiden',
        'Novice Stakes': 'maiden',

        'Handicap Hurdle': 'handicap',
        'Other Handicap': 'handicap',
        'Handicap Chase': 'handicap',
        'Selling Handicap': 'handicap',
        'Novice Hcap Chase': 'handicap',
        'Novice Hcap Hurdle': 'handicap',
        'Nursery': 'handicap',

        'Selling Stakes': 'stakes',
        'Claiming Stakes': 'stakes',
        'Classified Stakes': 'stakes',
        'Conditions Stakes': 'stakes',

        'Novice Hurdle': 'novice',
        'Novice Chase': 'novice',

        'Group 1': 'group',
        'Group 2': 'group',
        'Group 3': 'group',

        'Listed': 'listed',

        'Other Hurdle': 'hurdle',
        'Selling Hurdle': 'hurdle',

        'Other Chase': 'chase',

        'NH Flat': 'nh_flat',
        'Hunters Chase': 'hunters',
        'Amateur': 'amateur',
        'Unclassified': 'unclassified'
    }


    df['going_bin'] = df['Going'].map(going_bin_map)
    df['race_type_bin'] = df['Type'].map(race_type_bin_map)

    df.to_csv("preprocessed_before_form.csv")

    return df

