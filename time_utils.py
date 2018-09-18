import moment

def epoch_to_date(epoch):
  epoch_start = moment.now().replace(years=2016, months=1, days=1, hours=0, minutes=0, seconds=0, milliseconds=0)
  return epoch_start.add(days=epoch).format('YYYY-MM-DD')
